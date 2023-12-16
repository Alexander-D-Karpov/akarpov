from django.urls import path

from akarpov.music.api.views import (
    AddSongToPlaylistAPIView,
    DislikeSongAPIView,
    LikeSongAPIView,
    ListAlbumsAPIView,
    ListAuthorsAPIView,
    ListCreatePlaylistAPIView,
    ListCreateSongAPIView,
    ListDislikedSongsAPIView,
    ListenSongAPIView,
    ListLikedSongsAPIView,
    ListPublicPlaylistAPIView,
    ListSongPlaylistsAPIView,
    ListUserListenedSongsAPIView,
    RemoveSongFromPlaylistAPIView,
    RetrieveUpdateDestroyAlbumAPIView,
    RetrieveUpdateDestroyAuthorAPIView,
    RetrieveUpdateDestroyPlaylistAPIView,
    RetrieveUpdateDestroySongAPIView,
)

app_name = "music"

urlpatterns = [
    path("song/liked/", ListLikedSongsAPIView.as_view(), name="list_liked"),
    path("song/disliked/", ListDislikedSongsAPIView.as_view(), name="list_disliked"),
    path(
        "playlists/", ListCreatePlaylistAPIView.as_view(), name="list_create_playlist"
    ),
    path(
        "playlists/public/",
        ListPublicPlaylistAPIView.as_view(),
        name="list_public",
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
    path(
        "song/<str:slug>/playlists/",
        ListSongPlaylistsAPIView.as_view(),
        name="list_song_playlists",
    ),
    path("song/listen/", ListenSongAPIView.as_view(), name="listen-song"),
    path("song/listened/", ListUserListenedSongsAPIView.as_view(), name="listened"),
    path("song/like/", LikeSongAPIView.as_view(), name="like-song"),
    path("song/dislike/", DislikeSongAPIView.as_view(), name="dislike-song"),
    path(
        "playlists/add/",
        AddSongToPlaylistAPIView.as_view(),
        name="add-song-to-playlists",
    ),
    path(
        "playlists/remove/",
        RemoveSongFromPlaylistAPIView.as_view(),
        name="playlists-remove",
    ),
    path("albums/", ListAlbumsAPIView.as_view(), name="list_albums"),
    path(
        "albums/<str:slug>",
        RetrieveUpdateDestroyAlbumAPIView.as_view(),
        name="retrieve_update_delete_album",
    ),
    path("authors/", ListAuthorsAPIView.as_view(), name="list_authors"),
    path(
        "authors/<str:slug>",
        RetrieveUpdateDestroyAuthorAPIView.as_view(),
        name="retrieve_update_delete_author",
    ),
]
