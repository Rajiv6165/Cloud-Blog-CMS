from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Post, Tag, Comment, UserPostAccess, AuthorSubscription, Advertisement


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "slug"]
    list_display = ["name", "slug"]


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("user", "content", "is_approved", "sentiment", "created_at")
    readonly_fields = ("sentiment", "created_at")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "is_premium", "premium_price", "published_at", "created_at")
    list_filter = ("status", "is_premium", "tags", "created_at", "published_at")
    search_fields = ("title", "summary", "content")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("tags",)
    readonly_fields = ("image_size_comparison",)
    inlines = [CommentInline]
    date_hierarchy = "published_at"

    def image_size_comparison(self, obj):
        if obj.original_image_size and obj.compressed_image_size:
            before = obj.original_image_size / 1024
            after = obj.compressed_image_size / 1024
            savings = ((obj.original_image_size - obj.compressed_image_size) / obj.original_image_size) * 100
            return f"Original: {before:.1f} KB | Compressed: {after:.1f} KB (Saved {savings:.1f}%)"
        return "No cover image or not yet compressed."
    image_size_comparison.short_description = "Cover Image Compression Status"


@admin.register(UserPostAccess)
class UserPostAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "granted_at", "payment_reference")
    list_filter = ("granted_at",)
    search_fields = ("user__username", "user__email", "post__title")


@admin.register(AuthorSubscription)
class AuthorSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("subscriber", "author", "tier", "started_at", "is_active")
    list_filter = ("tier", "started_at", "is_active")
    search_fields = ("subscriber__username", "author__username")


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ("title", "position", "is_active", "impressions", "clicks", "ctr_display", "starts_at", "ends_at")
    list_filter = ("position", "is_active", "starts_at", "ends_at")
    search_fields = ("title", "destination_url")
    readonly_fields = ("impressions", "clicks")

    def ctr_display(self, obj):
        return f"{obj.ctr()}%"
    ctr_display.short_description = "CTR"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "is_approved", "sentiment_badge", "created_at")
    list_filter = ("is_approved", "sentiment", "created_at")
    search_fields = ("content",)
    readonly_fields = ("sentiment",)

    def sentiment_badge(self, obj):
        if not obj.sentiment:
            return mark_safe('<span style="color: #6b7280; font-size: 11px;">none</span>')
        val = obj.sentiment.lower()
        if val == "positive":
            return mark_safe('<span style="background-color: #d1fae5; color: #065f46; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase;">Positive</span>')
        elif val == "negative":
            return mark_safe('<span style="background-color: #fee2e2; color: #991b1b; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase;">Negative</span>')
        else:
            return mark_safe('<span style="background-color: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase;">Neutral</span>')
    sentiment_badge.short_description = "Sentiment"
