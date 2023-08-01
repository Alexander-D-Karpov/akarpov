from django.urls import path

from akarpov.blog.views import (
    comment,
    main_post_list_view,
    post_create_view,
    post_detail_view,
    post_list_view,
    post_update_view,
    rate_post_down,
    rate_post_up,
)

app_name = "blog"
urlpatterns = [
    path("", main_post_list_view, name="post_list"),
    path("all", post_list_view, name="all_posts_list"),
    path("p/<str:slug>", post_detail_view, name="post"),
    path("create/", post_create_view, name="post_create"),
    path("<str:slug>/edit", post_update_view, name="post_edit"),
    path("<str:slug>/comment", comment, name="comment"),
    path("<str:slug>/rate_up", rate_post_up, name="rate_post_up"),
    path("<str:slug>/rate_down", rate_post_down, name="rate_post_down"),
]
