from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, F
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.utils.translation import gettext as _
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    FormView,
)

from .models import Post, Tag, Comment, Profile, Advertisement
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
        from django.utils import timezone
        now = timezone.now()
        
        if self.request.user.is_authenticated:
            from .models import AuthorSubscription
            subscribed_author_ids = AuthorSubscription.objects.filter(
                subscriber=self.request.user,
                is_active=True,
                tier__in=["supporter", "patron"]
            ).values_list("author_id", flat=True)
            
            base_filter = Q(published_at__lte=now) | Q(author_id__in=subscribed_author_ids, early_access_at__lte=now) | Q(author=self.request.user)
        else:
            base_filter = Q(published_at__lte=now)

        queryset = Post.objects.filter(status="published").filter(base_filter).select_related("author").prefetch_related("tags").distinct()
        
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

    def get_object(self, queryset=None):
        from django.http import Http404
        from django.utils import timezone
        post = super().get_object(queryset)
        now = timezone.now()
        
        # Check early access visibility if post is scheduled for future publish
        if post.status == "published" and post.published_at and post.published_at > now:
            user = self.request.user
            if not user.is_authenticated:
                raise Http404("Post not found.")
            if user == post.author or user.is_staff or user.is_superuser:
                return post
            
            from .models import AuthorSubscription
            is_sub = AuthorSubscription.objects.filter(
                subscriber=user,
                author=post.author,
                is_active=True,
                tier__in=["supporter", "patron"]
            ).exists()
            
            if is_sub and post.early_access_at and post.early_access_at <= now:
                return post
            raise Http404("Post not found.")
        return post

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
            messages.error(request, _("You must unlock this premium post to leave comments."))
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
                messages.warning(request, _("Comment held for review."))
            else:
                messages.success(request, _("Comment posted successfully."))

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
            messages.error(request, _("Post not found."))
            return redirect("blog:post_list")

        UserPostAccess.objects.get_or_create(
            user=request.user,
            post=post,
            defaults={"payment_reference": "FREE_UNLOCK_PLACEHOLDER"}
        )
        messages.success(request, _("Successfully unlocked the premium post: %(title)s") % {'title': post.title})
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
        
        from django.utils import timezone
        now = timezone.now()
        posts_qs = Post.objects.filter(author=self.object, status="published")
        
        user = self.request.user
        is_subscriber = False
        sub_tier = None
        
        if user.is_authenticated:
            from .models import AuthorSubscription
            try:
                sub = AuthorSubscription.objects.get(subscriber=user, author=self.object, is_active=True)
                is_subscriber = True
                sub_tier = sub.tier
            except AuthorSubscription.DoesNotExist:
                pass
            
            if user == self.object or user.is_staff or user.is_superuser:
                # View all posts
                pass
            elif is_subscriber and sub_tier in ["supporter", "patron"]:
                posts_qs = posts_qs.filter(Q(published_at__lte=now) | Q(early_access_at__lte=now))
            else:
                posts_qs = posts_qs.filter(published_at__lte=now)
        else:
            posts_qs = posts_qs.filter(published_at__lte=now)
            
        context["posts"] = posts_qs.select_related("author").prefetch_related("tags").distinct()
        profile, _ = Profile.objects.get_or_create(user=self.object)
        context["profile"] = profile
        context["is_subscriber"] = is_subscriber
        context["sub_tier"] = sub_tier
        return context


class SubscribeToAuthorView(LoginRequiredMixin, View):
    def post(self, request, username, *args, **kwargs):
        from .models import AuthorSubscription
        User = get_user_model()
        try:
            author = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({"success": False, "error": _("Author not found")}, status=404)
        
        if author == request.user:
            return JsonResponse({"success": False, "error": _("You cannot subscribe to yourself")}, status=400)
        
        tier = request.POST.get("tier", "free")
        if not tier and request.body:
            try:
                import json
                data = json.loads(request.body)
                tier = data.get("tier", "free")
            except Exception:
                pass
                
        if tier not in ["free", "supporter", "patron"]:
            return JsonResponse({"success": False, "error": _("Invalid tier name")}, status=400)
            
        sub, created = AuthorSubscription.objects.get_or_create(
            subscriber=request.user,
            author=author,
            defaults={"tier": tier, "is_active": True}
        )
        if not created:
            sub.tier = tier
            sub.is_active = True
            sub.save()
            
        return JsonResponse({
            "success": True,
            "tier": tier,
            "message": _("Successfully subscribed to %(username)s as a %(tier)s!") % {'username': author.username, 'tier': tier}
        })


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


class AdServeView(View):
    def get(self, request, pk, *args, **kwargs):
        ad = get_object_or_404(Advertisement, pk=pk)
        Advertisement.objects.filter(pk=pk).update(clicks=F("clicks") + 1)
        return redirect(ad.destination_url)
