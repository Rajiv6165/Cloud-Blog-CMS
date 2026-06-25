from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import Post, Comment, Tag

User = get_user_model()

INPUT_CLASS = "w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-500"


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": INPUT_CLASS, "placeholder": "Email address"}
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": INPUT_CLASS, "placeholder": "Username"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": INPUT_CLASS, "placeholder": "Password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": INPUT_CLASS, "placeholder": "Confirm password"}
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            "title",
            "slug",
            "summary",
            "content",
            "tags",
            "status",
            "allow_comments",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input input-bordered w-full", "placeholder": "Post title"}),
            "slug": forms.TextInput(attrs={"class": "input input-bordered w-full", "placeholder": "auto or custom"}),
            "summary": forms.TextInput(attrs={"class": "input input-bordered w-full", "placeholder": "Short summary"}),
            "content": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full min-h-56", "placeholder": "Write your content..."}),
            "tags": forms.SelectMultiple(attrs={"class": "select select-bordered w-full"}),
            "status": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3, "placeholder": "Add a comment"}),
        }
