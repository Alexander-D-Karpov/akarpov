from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    Album,
    Author,
    Playlist,
    PlaylistSong,
    RadioSong,
    Song,
    SongInQue,
    SongUserRating,
    TempFileUpload,
    UserListenHistory,
)


class JSONFieldAdmin(admin.ModelAdmin):
    def render_meta_field(self, obj):
        meta = obj.meta
        if not meta:
            return "No data"
        html_content = (
            "<div style='max-height: 200px; overflow-y: scroll;'><pre>{}</pre></div>"
        )
        return format_html(html_content, mark_safe(meta))

    readonly_fields = ("render_meta_field",)


class PlaylistSongInline(admin.TabularInline):
    model = PlaylistSong
    extra = 1


class SongUserRatingInline(admin.TabularInline):
    model = SongUserRating
    extra = 1


class UserListenHistoryInline(admin.TabularInline):
    model = UserListenHistory
    extra = 1


class SongInQueInline(admin.TabularInline):
    model = SongInQue
    extra = 1


class SongInline(admin.TabularInline):
    model = Song
    extra = 1


class AuthorAdmin(JSONFieldAdmin):
    list_display = ("name", "slug")
    search_fields = ["name"]

    def render_meta_field(self, obj):
        meta = super().render_meta_field(obj)
        return meta


admin.site.register(Author, AuthorAdmin)


class AlbumAdmin(JSONFieldAdmin):
    list_display = ("name", "link")
    search_fields = ["name"]
    inlines = [SongInline]

    def render_meta_field(self, obj):
        meta = super().render_meta_field(obj)
        return meta


admin.site.register(Album, AlbumAdmin)


class SongAdmin(JSONFieldAdmin):
    list_display = ("name", "link", "length", "played")
    search_fields = ["name", "authors__name", "album__name"]
    inlines = [PlaylistSongInline, SongUserRatingInline, UserListenHistoryInline]

    def render_meta_field(self, obj):
        meta = super().render_meta_field(obj)
        return meta


admin.site.register(Song, SongAdmin)


class PlaylistAdmin(admin.ModelAdmin):
    list_display = ("name", "private", "creator", "length")
    search_fields = ["name", "creator__username"]
    inlines = [PlaylistSongInline]


admin.site.register(Playlist, PlaylistAdmin)


class PlaylistSongAdmin(admin.ModelAdmin):
    list_display = ("playlist", "song", "order")
    search_fields = ["playlist__name", "song__name"]


admin.site.register(PlaylistSong, PlaylistSongAdmin)


class SongInQueAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "error")
    search_fields = ["name"]


admin.site.register(SongInQue, SongInQueAdmin)


class TempFileUploadAdmin(admin.ModelAdmin):
    list_display = ("file",)
    search_fields = ["file"]


admin.site.register(TempFileUpload, TempFileUploadAdmin)


class RadioSongAdmin(admin.ModelAdmin):
    list_display = ("start", "slug", "song")
    search_fields = ["song__name", "slug"]


admin.site.register(RadioSong, RadioSongAdmin)


class SongUserRatingAdmin(admin.ModelAdmin):
    list_display = ("song", "user", "like", "created")
    search_fields = ["song__name", "user__username"]


admin.site.register(SongUserRating, SongUserRatingAdmin)


class UserListenHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "song", "created")
    search_fields = ["user__username", "song__name"]


admin.site.register(UserListenHistory, UserListenHistoryAdmin)
