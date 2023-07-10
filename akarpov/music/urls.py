from django.urls import path

from . import views

app_name = "music"

urlpatterns = [
    path("upload", views.load_track_view, name="load"),
    path("upload_file", views.load_track_file_view, name="upload"),
    path("<str:slug>", views.song_view, name="song"),
    path("album/<str:slug>", views.album_view, name="album"),
    path("author/<str:slug>", views.author_view, name="author"),
    path("playlist/<str:slug>", views.playlist_view, name="playlist"),
    path("radio/", views.radio_main_view, name="radio"),
]
