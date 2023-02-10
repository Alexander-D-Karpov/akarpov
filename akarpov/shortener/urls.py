from django.urls import path

from akarpov.shortener.views import link_detail_view, short_link_create_view

app_name = "shortener"

urlpatterns = [
    path("", short_link_create_view, name="create"),
    path("<str:slug>", link_detail_view, name="view"),
]
