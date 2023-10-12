from django.urls import path

from akarpov.music.api.views import (
    ListCreatePlaylistAPIView,
    ListCreateSongAPIView,
    RetrieveUpdateDestroyPlaylistAPIView,
    RetrieveUpdateDestroySongAPIView,
)

app_name = "music"

urlpatterns = [
    path(
        "playlists/", ListCreatePlaylistAPIView.as_view(), name="list_create_playlist"
    ),
    path(
        "playlists/<str:slug>",
        RetrieveUpdateDestroyPlaylistAPIView.as_view(),
        name="retrieve_update_delete_playlist",
    ),
    path("song/", ListCreateSongAPIView.as_view(), name="list_create_song"),
    path(
        "song/<str:slug>",
        RetrieveUpdateDestroySongAPIView.as_view(),
        name="retrieve_update_delete_song",
    ),
]
