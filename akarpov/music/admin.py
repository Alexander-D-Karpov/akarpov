from django.contrib import admin

from akarpov.music.models import (
    Album,
    Author,
    Playlist,
    PlaylistSong,
    Song,
    SongUserRating,
)

admin.site.register(Author)
admin.site.register(Album)
admin.site.register(Song)
admin.site.register(Playlist)
admin.site.register(PlaylistSong)
admin.site.register(SongUserRating)
