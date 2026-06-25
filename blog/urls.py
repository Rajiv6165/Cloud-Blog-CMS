from django.urls import path
from . import views


urlpatterns = [
    path("", views.PostListView.as_view(), name="post_list"),
    path("tag/<slug:slug>/", views.TagDetailView.as_view(), name="tag_detail"),
    path("post/create/", views.PostCreateView.as_view(), name="post_create"),
    path("post/<slug:slug>/", views.PostDetailView.as_view(), name="post_detail"),
    path("post/<slug:slug>/edit/", views.PostUpdateView.as_view(), name="post_update"),
    path("post/<slug:slug>/delete/", views.PostDeleteView.as_view(), name="post_delete"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("profile/", views.ProfileEditView.as_view(), name="profile_edit"),
    path("comment/<int:pk>/delete/", views.CommentDeleteView.as_view(), name="comment_delete"),
]

