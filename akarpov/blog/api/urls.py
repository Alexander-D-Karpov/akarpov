from django.urls import path

from akarpov.blog.api.views import (
    GetPost,
    ListCommentsSerializer,
    ListMainPostsView,
    ListPostsView,
)

app_name = "blog_api"

urlpatterns = [
    path("", ListMainPostsView.as_view(), name="list_main"),
    path("all/", ListPostsView.as_view(), name="list_all"),
    path("<str:slug>", GetPost.as_view(), name="post"),
    path("<str:slug>/comments", ListCommentsSerializer.as_view(), name="post_comments"),
]
