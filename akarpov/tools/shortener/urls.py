from django.urls import path

from akarpov.tools.shortener.views import short_link_create_view

app_name = "shortener"

urlpatterns = [
    path("", short_link_create_view, name="create"),
    path("revoked", short_link_create_view, name="revoked"),
]
