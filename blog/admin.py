from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Post, Tag, Comment


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
    list_display = ("title", "author", "status", "published_at", "created_at")
    list_filter = ("status", "tags", "created_at", "published_at")
    search_fields = ("title", "summary", "content")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("tags",)
    inlines = [CommentInline]
    date_hierarchy = "published_at"


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
