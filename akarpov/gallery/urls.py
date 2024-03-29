from django.urls import path

from akarpov.gallery.views import (
    collection_view,
    image_upload_view,
    image_view,
    list_collections_view,
    list_tag_images_view,
)

app_name = "gallery"
urlpatterns = [
    path("", list_collections_view, name="list"),
    path("upload/", image_upload_view, name="upload"),
    path("<str:slug>", collection_view, name="collection"),
    path("tag/<str:slug>", list_tag_images_view, name="tag"),
    path("image/<str:slug>", image_view, name="view"),
]
