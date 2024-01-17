import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse

from akarpov.common.models import BaseImageModel
from akarpov.tools.shortener.models import ShortLinkModel
from akarpov.users.services.history import UserHistoryModel
from akarpov.utils.cache import cache_model_property


class Author(BaseImageModel, ShortLinkModel):
    name = models.CharField(max_length=200, unique=True)
    link = models.URLField(blank=True)
    meta = models.JSONField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse("music:author", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


class Album(BaseImageModel, ShortLinkModel):
    name = models.CharField(max_length=200, unique=True)
    link = models.URLField(blank=True)
    meta = models.JSONField(blank=True, null=True)
    authors = models.ManyToManyField("Author", related_name="albums")

    def get_absolute_url(self):
        return reverse("music:album", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


class Song(BaseImageModel, ShortLinkModel):
    link = models.URLField(blank=True)
    length = models.IntegerField(null=True)
    played = models.IntegerField(default=0)
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to="music")
    authors = models.ManyToManyField("Author", related_name="songs")
    album = models.ForeignKey(
        Album, null=True, related_name="songs", on_delete=models.SET_NULL
    )
    creator = models.ForeignKey(
        "users.User", related_name="songs", on_delete=models.SET_NULL, null=True
    )
    created = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(blank=True, null=True)
    likes = models.IntegerField(default=0)
    volume = ArrayField(models.IntegerField(), null=True)

    def get_absolute_url(self):
        return reverse("music:song", kwargs={"slug": self.slug})

    @property
    def full_props(self):
        if self.album_name and self.artists_names:
            return f"{self.album_name} - {self.artists_names}"
        elif self.album_name:
            return self.album_name
        elif self.artists_names:
            return self.artists_names
        return ""

    @property
    def _album_name(self):
        if self.album and self.album.name:
            return self.album.name
        return ""

    @property
    def _authors_names(self):
        if self.authors:
            return ", ".join(self.authors.values_list("name", flat=True))
        return ""

    @property
    def album_name(self):
        return cache_model_property(self, "_album_name")

    @property
    def artists_names(self):
        return cache_model_property(self, "_authors_names")

    def __str__(self):
        return self.name

    class SlugMeta:
        slug_length = 10


class Playlist(ShortLinkModel, UserHistoryModel):
    name = models.CharField(max_length=200)
    private = models.BooleanField(default=True)
    creator = models.ForeignKey(
        "users.User", related_name="playlists", on_delete=models.CASCADE
    )
    length = models.IntegerField(default=0)

    def get_absolute_url(self):
        return reverse("music:playlist", kwargs={"slug": self.slug})

    def get_songs(self):
        return self.songs.all().values("song")

    class Meta:
        verbose_name = "Playlist"


class PlaylistSong(models.Model):
    order = models.IntegerField()
    playlist = models.ForeignKey(
        "Playlist", related_name="songs", on_delete=models.CASCADE
    )
    song = models.ForeignKey("Song", related_name="playlists", on_delete=models.CASCADE)

    class Meta:
        unique_together = [("playlist", "song"), ("playlist", "order")]
        ordering = ["order"]


class SongInQue(models.Model):
    name = models.CharField(blank=True, max_length=500)
    status = models.CharField(null=True, blank=True, max_length=500)
    error = models.BooleanField(default=False)


class TempFileUpload(models.Model):
    file = models.FileField(upload_to="music_tmp")


class RadioSong(models.Model):
    start = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True)
    song = models.ForeignKey("Song", related_name="radio", on_delete=models.CASCADE)


class SongUserRating(models.Model):
    song = models.ForeignKey(
        "Song", related_name="user_likes", on_delete=models.PROTECT
    )
    user = models.ForeignKey(
        "users.User", related_name="song_likes", on_delete=models.CASCADE
    )
    like = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.song} {'like' if self.like else 'dislike'}"

    class Meta:
        unique_together = ["song", "user"]
        ordering = ["-created"]


class AnonMusicUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"AnonMusicUser {self.id}"


class AnonMusicUserHistory(models.Model):
    user = models.ForeignKey(
        "music.AnonMusicUser", related_name="songs_listened", on_delete=models.CASCADE
    )
    song = models.ForeignKey(
        "Song", related_name="anon_listeners", on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.user} - {self.song}"


class UserListenHistory(models.Model):
    user = models.ForeignKey(
        "users.User", related_name="songs_listened", on_delete=models.CASCADE
    )
    song = models.ForeignKey("Song", related_name="listeners", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]


class UserMusicProfile(models.Model):
    user = models.OneToOneField(
        "users.User", related_name="music_profile", on_delete=models.CASCADE
    )
    lastfm_username = models.CharField(max_length=50, blank=True, null=True)
    lastfm_token = models.CharField(max_length=50, blank=True, null=True)
    preferences = models.JSONField(null=True)

    def __str__(self):
        return f"{self.user} music profile"
