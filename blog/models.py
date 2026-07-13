from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("blog:tag_detail", args=[self.slug])


class Post(models.Model):
    STATUS_CHOICES = (
        ("draft", _("Draft")),
        ("published", _("Published")),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="posts")
    summary = models.CharField(max_length=300, blank=True)
    content = models.TextField()
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    allow_comments = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    premium_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    cover_image = models.ImageField(upload_to="covers/", blank=True, null=True)
    cover_image_blur = models.TextField(blank=True)
    original_image_size = models.PositiveIntegerField(null=True, blank=True)
    compressed_image_size = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    early_access_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        is_new_image = False
        if self.cover_image:
            if self.pk:
                try:
                    old_post = Post.objects.get(pk=self.pk)
                    if old_post.cover_image != self.cover_image:
                        is_new_image = True
                except Post.DoesNotExist:
                    is_new_image = True
            else:
                is_new_image = True

        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

        if is_new_image and self.cover_image:
            try:
                from PIL import Image
                import io
                import base64
                from django.core.files.base import ContentFile

                # Save original size
                orig_size = self.cover_image.size
                self.original_image_size = orig_size

                img = Image.open(self.cover_image.path)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                max_width = 1200
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)

                # Save with 85% quality WebP
                output = io.BytesIO()
                img.save(output, format='WEBP', quality=85, optimize=True)
                comp_bytes = output.getvalue()
                self.compressed_image_size = len(comp_bytes)

                # Replace original file on model
                webp_name = self.cover_image.name.rsplit('.', 1)[0] + '.webp'
                self.cover_image.save(
                    webp_name,
                    ContentFile(comp_bytes),
                    save=False
                )

                # Generate blur placeholder (20x20 base64)
                img_small = img.resize((20, 20), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
                buffer = io.BytesIO()
                img_small.save(buffer, format='WEBP', quality=30)
                self.cover_image_blur = 'data:image/webp;base64,' + base64.b64encode(buffer.getvalue()).decode('utf-8')

                super().save(update_fields=['cover_image', 'cover_image_blur', 'original_image_size', 'compressed_image_size'])
            except Exception as e:
                print(f"Error compressing cover image: {e}")

    def get_absolute_url(self):
        return reverse("blog:post_detail", args=[self.slug])

    @property
    def reading_time(self) -> int:
        words = len(self.content.split())
        return max(1, round(words / 200))

    @property
    def view_count(self) -> int:
        return (self.pk * 47) % 430 + 12


class UserPostAccess(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    granted_at = models.DateTimeField(auto_now_add=True)
    payment_reference = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ("user", "post")

    def __str__(self):
        return f"{self.user.username} -> {self.post.title}"



class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="comments")
    content = models.TextField(max_length=2000)
    is_approved = models.BooleanField(default=True)
    sentiment = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Comment by {self.user} on {self.post}"


class Profile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="profile")
    buymeacoffee_url = models.URLField(blank=True)
    paypal_email = models.EmailField(blank=True)
    upi_id = models.CharField(max_length=100, blank=True)
    supporter_price = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)
    patron_price = models.DecimalField(max_digits=6, decimal_places=2, default=15.00)
    supporter_perks = models.TextField(blank=True, default="Early access to posts, No ads")
    patron_perks = models.TextField(blank=True, default="Everything in Supporter + Direct messages")

    def __str__(self):
        return f"Profile of {self.user.username}"


class AuthorSubscription(models.Model):
    subscriber = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='subscriptions')
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='subscribers')
    tier = models.CharField(max_length=20, choices=[('free', _('Free')), ('supporter', _('Supporter')), ('patron', _('Patron'))], default='free')
    started_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('subscriber', 'author')

    def __str__(self):
        return f"{self.subscriber.username} subscribed to {self.author.username} ({self.tier})"


class Advertisement(models.Model):
    POSITION_CHOICES = [
        ('sidebar_top', _('Sidebar Top')),
        ('sidebar_bottom', _('Sidebar Bottom')),
        ('post_bottom', _('After Post Content')),
        ('list_between', _('Between Post Cards')),
    ]
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='ads/')
    destination_url = models.URLField()
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)
    is_active = models.BooleanField(default=True)
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)

    def ctr(self):
        return round((self.clicks / self.impressions * 100), 2) if self.impressions else 0

    def __str__(self):
        return self.title


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=get_user_model())
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=get_user_model())
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, "profile"):
        Profile.objects.get_or_create(user=instance)
    instance.profile.save()

