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
    UserMusicProfile,
)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "id")
    search_fields = ["name", "slug"]
    list_per_page = 50
    show_full_result_count = False
    readonly_fields = ("render_meta_field",)

    def render_meta_field(self, obj):
        if not obj.meta:
            return "No data"
        return format_html(
            "<div style='max-height: 200px; overflow-y: scroll;'><pre>{}</pre></div>",
            mark_safe(str(obj.meta)),
        )


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "id", "author_count")
    search_fields = ["name", "slug"]
    list_per_page = 50
    show_full_result_count = False
    readonly_fields = ("render_meta_field",)
    raw_id_fields = ("authors",)
    filter_horizontal = ()

    def author_count(self, obj):
        return obj.authors.count()

    author_count.short_description = "Authors"

    def render_meta_field(self, obj):
        if not obj.meta:
            return "No data"
        return format_html(
            "<div style='max-height: 200px; overflow-y: scroll;'><pre>{}</pre></div>",
            mark_safe(str(obj.meta)),
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("authors")


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "length", "played", "likes", "created")
    search_fields = ["name", "slug"]
    list_filter = ("created",)
    list_per_page = 50
    show_full_result_count = False
    readonly_fields = ("render_meta_field", "played", "likes", "length", "volume")
    raw_id_fields = ("authors", "album", "creator")
    date_hierarchy = "created"

    fieldsets = (
        (None, {"fields": ("name", "slug", "file", "image", "link")}),
        ("Relations", {"fields": ("authors", "album", "creator")}),
        ("Stats", {"fields": ("length", "played", "likes", "volume")}),
        ("Meta", {"fields": ("meta", "render_meta_field")}),
    )

    def render_meta_field(self, obj):
        if not obj.meta:
            return "No data"
        return format_html(
            "<div style='max-height: 200px; overflow-y: scroll;'><pre>{}</pre></div>",
            mark_safe(str(obj.meta)),
        )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("album", "creator")


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ("name", "private", "creator", "length")
    search_fields = ["name", "creator__username"]
    list_per_page = 50
    show_full_result_count = False
    raw_id_fields = ("creator",)
    list_select_related = ("creator",)


@admin.register(PlaylistSong)
class PlaylistSongAdmin(admin.ModelAdmin):
    list_display = ("playlist", "song", "order")
    search_fields = ["playlist__name", "song__name"]
    list_per_page = 50
    show_full_result_count = False
    raw_id_fields = ("playlist", "song")
    list_select_related = ("playlist", "song")


@admin.register(SongInQue)
class SongInQueAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "error")
    search_fields = ["name"]
    list_per_page = 50
    list_filter = ("error",)


@admin.register(TempFileUpload)
class TempFileUploadAdmin(admin.ModelAdmin):
    list_display = ("file", "id")
    list_per_page = 50


@admin.register(RadioSong)
class RadioSongAdmin(admin.ModelAdmin):
    list_display = ("start", "slug", "song")
    search_fields = ["song__name", "slug"]
    list_per_page = 50
    raw_id_fields = ("song",)
    list_select_related = ("song",)


@admin.register(SongUserRating)
class SongUserRatingAdmin(admin.ModelAdmin):
    list_display = ("song", "user", "like", "created")
    search_fields = ["song__name", "user__username"]
    list_per_page = 50
    show_full_result_count = False
    raw_id_fields = ("song", "user")
    list_select_related = ("song", "user")
    list_filter = ("like", "created")


@admin.register(UserListenHistory)
class UserListenHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "song", "created")
    search_fields = ["user__username", "song__name"]
    list_per_page = 50
    show_full_result_count = False
    raw_id_fields = ("user", "song")
    list_select_related = ("user", "song")
    date_hierarchy = "created"


@admin.register(UserMusicProfile)
class UserMusicProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "lastfm_username")
    search_fields = ["user__username", "lastfm_username"]
    list_per_page = 50
    raw_id_fields = ("user",)
    list_select_related = ("user",)
