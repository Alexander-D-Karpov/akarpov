from django.urls import path

from akarpov.music.api.views import (
    ListCreatePlaylistAPIView,
    ListCreateSongAPIView,
    RetrieveUpdateDestroyPlaylistAPIView,
    RetrieveUpdateDestroySongAPIView,
)

app_name = "music"

urlpatterns = [
    path("playlists/", ListCreatePlaylistAPIView.as_view()),
    path("playlists/<str:slug>", RetrieveUpdateDestroyPlaylistAPIView.as_view()),
    path("song/", ListCreateSongAPIView.as_view()),
    path("song/<str:slug>", RetrieveUpdateDestroySongAPIView.as_view()),
]
