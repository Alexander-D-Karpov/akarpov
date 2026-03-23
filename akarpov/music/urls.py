from django.urls import path

from . import views

app_name = "music"

urlpatterns = [
    path("", views.music_landing, name="landing"),
    path("downloads/", views.downloads_view, name="downloads"),
    path("upload", views.downloads_view, name="upload"),
    path("upload_file", views.downloads_view, name="upload_file"),
    path("cookies/", views.cookies_view, name="cookies"),
    path("<str:slug>", views.song_view, name="song"),
    path("album/<str:slug>", views.album_view, name="album"),
    path("author/<str:slug>", views.author_view, name="author"),
    path("playlist/<str:slug>", views.playlist_view, name="playlist"),
    path("radio/", views.radio_main_view, name="radio"),
    path("player/", views.music_player_view, name="player"),
    path("lastfm/callback", views.lastfm_callback, name="lastfm_callback"),
    path("lastfm/connect", views.lastfm_auth, name="lastfm_connect"),
]
