from django.contrib import admin
from .models import Post, Tag, Comment


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "slug"]
    list_display = ["name", "slug"]


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("user", "content", "is_approved", "created_at")
    readonly_fields = ("created_at",)


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
    list_display = ("post", "user", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("content",)
