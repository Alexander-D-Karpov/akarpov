from django.contrib import admin

from akarpov.music.models import Album, Author, Playlist, PlaylistSong, Song

admin.site.register(Author)
admin.site.register(Album)
admin.site.register(Song)
admin.site.register(Playlist)
admin.site.register(PlaylistSong)
