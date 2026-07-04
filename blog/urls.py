from django.urls import path
from . import views
from . import ai_views

urlpatterns = [
    path("", views.PostListView.as_view(), name="post_list"),
    path("tag/<slug:slug>/", views.TagDetailView.as_view(), name="tag_detail"),
    path("post/create/", views.PostCreateView.as_view(), name="post_create"),
    path("post/<slug:slug>/", views.PostDetailView.as_view(), name="post_detail"),
    path("post/<slug:slug>/edit/", views.PostUpdateView.as_view(), name="post_update"),
    path("post/<slug:slug>/delete/", views.PostDeleteView.as_view(), name="post_delete"),
    path("post/<slug:slug>/unlock/", views.GrantAccessView.as_view(), name="post_unlock"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("profile/", views.ProfileEditView.as_view(), name="profile_edit"),
    path("author/<str:username>/", views.AuthorDetailView.as_view(), name="author_detail"),
    path("author/<str:username>/subscribe/", views.SubscribeToAuthorView.as_view(), name="author_subscribe"),
    path("comment/<int:pk>/delete/", views.CommentDeleteView.as_view(), name="comment_delete"),
    path("ai/assist/", ai_views.AIAssistView.as_view(), name="ai_assist"),
    path("ai/summarize/", ai_views.AISummarizeView.as_view(), name="ai_summarize"),
    path("ai/suggest-tags/", ai_views.AITagSuggestView.as_view(), name="ai_suggest_tags"),
    path("ai/create-tag/", ai_views.AICreateTagView.as_view(), name="ai_create_tag"),
    path("ai/related/<slug:slug>/", ai_views.AIRelatedView.as_view(), name="ai_related"),
]
