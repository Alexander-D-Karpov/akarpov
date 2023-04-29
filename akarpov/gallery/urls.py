from django.urls import path

from akarpov.gallery.views import collection_view, image_view, list_collections_view

app_name = "gallery"
urlpatterns = [
    path("", list_collections_view, name="list"),
    path("<str:slug>", collection_view, name="collection"),
    path("image/<str:slug>", image_view, name="view"),
]
