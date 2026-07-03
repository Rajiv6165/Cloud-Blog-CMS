from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import Post, Comment, Tag, Profile

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


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Your first name..."}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Your last name..."}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": INPUT_CLASS, "placeholder": "you@example.com"}))

    buymeacoffee_url = forms.URLField(required=False, widget=forms.URLInput(attrs={"class": INPUT_CLASS, "placeholder": "https://buymeacoffee.com/yourusername"}))
    paypal_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": INPUT_CLASS, "placeholder": "yourname@paypal.com"}))
    upi_id = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "username@upi"}))

    class Meta:
        model = Profile
        fields = ["buymeacoffee_url", "paypal_email", "upi_id"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["first_name"].initial = self.user.first_name
            self.fields["last_name"].initial = self.user.last_name
            self.fields["email"].initial = self.user.email

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.exclude(pk=self.user.pk).filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def clean_upi_id(self):
        upi_id = self.cleaned_data.get("upi_id")
        if upi_id and "@" not in upi_id:
            raise forms.ValidationError("Invalid UPI ID format. Should be like username@upi.")
        return upi_id

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data["first_name"]
            self.user.last_name = self.cleaned_data["last_name"]
            self.user.email = self.cleaned_data["email"]
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile

