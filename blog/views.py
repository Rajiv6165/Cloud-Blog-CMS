from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    FormView,
)

from .models import Post, Tag, Comment, Profile
from .forms import PostForm, CommentForm, RegisterForm, UserProfileForm


class RegisterView(FormView):
    template_name = "registration/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("blog:post_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("blog:post_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class PostListView(ListView):
    model = Post
    paginate_by = 10
    template_name = "blog/post_list.html"

    def get_queryset(self):
        queryset = Post.objects.filter(status="published").select_related("author").prefetch_related("tags")
        query = self.request.GET.get("q")
        tag_slug = self.request.GET.get("tag")
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(content__icontains=query)
            )
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["tags"] = Tag.objects.all()
        context["query"] = self.request.GET.get("q", "")
        context["active_tag"] = self.request.GET.get("tag")
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Post.objects.select_related("author").prefetch_related("tags", "comments__user")

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        if not self.object.allow_comments:
            return redirect(self.object.get_absolute_url())
        
        # Access control check for commenting on premium posts
        has_access = True
        if self.object.is_premium:
            if not request.user.is_authenticated:
                has_access = False
            elif request.user == self.object.author or request.user.is_staff or request.user.is_superuser:
                has_access = True
            else:
                from .models import UserPostAccess
                has_access = UserPostAccess.objects.filter(user=request.user, post=self.object).exists()

        if not has_access:
            messages.error(request, "You must unlock this premium post to leave comments.")
            return redirect(self.object.get_absolute_url())

        form = CommentForm(request.POST)
        if request.user.is_authenticated and form.is_valid():
            content = form.cleaned_data["content"]
            
            # Moderation check
            from .ai_views import AIModerateView
            spam, sentiment, toxic = AIModerateView.moderate_comment(content)
            
            is_approved = True
            if spam or toxic:
                is_approved = False
                messages.warning(request, "Comment held for review.")
            else:
                messages.success(request, "Comment posted successfully.")

            Comment.objects.create(
                post=self.object,
                user=request.user,
                content=content,
                is_approved=is_approved,
                sentiment=sentiment,
            )
            return HttpResponseRedirect(self.object.get_absolute_url())
        context = self.get_context_data(object=self.object)
        context["form"] = form
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()

        # Access control check
        post = self.object
        user = self.request.user
        has_access = True
        if post.is_premium:
            if not user.is_authenticated:
                has_access = False
            elif user == post.author or user.is_staff or user.is_superuser:
                has_access = True
            else:
                from .models import UserPostAccess
                has_access = UserPostAccess.objects.filter(user=user, post=post).exists()

        context["has_access"] = has_access
        if not has_access:
            teaser_words = post.content.split()[:200]
            context["teaser_content"] = " ".join(teaser_words)

        if self.object.tags.exists():
            context["related"] = (
                Post.objects.filter(status="published", tags__in=self.object.tags.all())
                .exclude(pk=self.object.pk)
                .distinct()[:4]
            )
        else:
            context["related"] = []
        return context


class GrantAccessView(LoginRequiredMixin, View):
    def post(self, request, slug, *args, **kwargs):
        from .models import UserPostAccess
        try:
            post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            messages.error(request, "Post not found.")
            return redirect("blog:post_list")

        UserPostAccess.objects.get_or_create(
            user=request.user,
            post=post,
            defaults={"payment_reference": "FREE_UNLOCK_PLACEHOLDER"}
        )
        messages.success(request, f"Successfully unlocked the premium post: {post.title}")
        return redirect(post.get_absolute_url())


class AuthorOrStaffRequiredMixin(UserPassesTestMixin):
    def test_func(self) -> bool | None:
        obj: Post = getattr(self, "object", None)
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        if obj is None:
            return True
        return obj.author_id == user.id


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, AuthorOrStaffRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"


class PostDeleteView(LoginRequiredMixin, AuthorOrStaffRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/post_confirm_delete.html"
    success_url = reverse_lazy("blog:post_list")
    slug_field = "slug"
    slug_url_kwarg = "slug"


class TagDetailView(DetailView):
    model = Tag
    template_name = "blog/tag_detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["posts"] = (
            Post.objects.filter(status="published", tags=self.object)
            .select_related("author")
            .prefetch_related("tags")
        )
        return context


class DashboardView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "blog/dashboard.html"
    context_object_name = "posts"
    paginate_by = 15

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user).order_by("-updated_at")


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = UserProfileForm
    template_name = "blog/profile_edit.html"
    success_url = reverse_lazy("blog:post_list")

    def get_object(self, queryset=None):
        profile, _ = Profile.objects.select_related("user").get_or_create(user=self.request.user)
        return profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class AuthorDetailView(DetailView):
    model = get_user_model()
    template_name = "blog/author_detail.html"
    slug_field = "username"
    slug_url_kwarg = "username"
    context_object_name = "author"

    def get_queryset(self):
        return get_user_model().objects.all()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["posts"] = (
            Post.objects.filter(author=self.object, status="published")
            .select_related("author")
            .prefetch_related("tags")
        )
        profile, _ = Profile.objects.get_or_create(user=self.object)
        context["profile"] = profile
        return context


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment

    def get(self, request, *args, **kwargs):
        # Allow instant comment deletion on GET request if confirmed via browser popup
        return self.post(request, *args, **kwargs)

    def get_success_url(self):
        return self.object.post.get_absolute_url()

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.user or self.request.user.is_staff
