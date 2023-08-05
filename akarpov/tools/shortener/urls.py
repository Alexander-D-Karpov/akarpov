from django.urls import path

from akarpov.tools.shortener.views import (
    link_detail_view,
    link_public_detail_view,
    short_link_create_view,
)

app_name = "shortener"

urlpatterns = [
    path("", short_link_create_view, name="create"),
    path("<str:slug>", link_detail_view, name="view"),
    path("p/<str:slug>", link_public_detail_view, name="public_view"),
    path("revoked", short_link_create_view, name="revoked"),
]
