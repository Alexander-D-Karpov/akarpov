from django.urls import path

from . import views

app_name = "music"

urlpatterns = [
    path("", views.music_landing, name="landing"),
    path("upload", views.load_track_view, name="load"),
    path("upload_file", views.load_track_file_view, name="upload"),
    path("<str:slug>", views.song_view, name="song"),
    path("album/<str:slug>", views.album_view, name="album"),
    path("author/<str:slug>", views.author_view, name="author"),
    path("playlist/<str:slug>", views.playlist_view, name="playlist"),
    path("radio/", views.radio_main_view, name="radio"),
    path("player/", views.music_player_view, name="player"),
    path("lastfm/callback", views.lastfm_callback, name="lastfm_callback"),
    path("lastfm/connect", views.lastfm_auth, name="lastfm_connect"),
]
