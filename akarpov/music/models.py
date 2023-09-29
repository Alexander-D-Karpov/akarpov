from django.db import models
from django.urls import reverse

from akarpov.common.models import BaseImageModel
from akarpov.tools.shortener.models import ShortLinkModel
from akarpov.users.services.history import UserHistoryModel


class Author(BaseImageModel, ShortLinkModel):
    name = models.CharField(max_length=200)
    link = models.URLField(blank=True)

    def get_absolute_url(self):
        return reverse("music:author", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


class Album(BaseImageModel, ShortLinkModel):
    name = models.CharField(max_length=200)
    link = models.URLField(blank=True)

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
    meta = models.JSONField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse("music:song", kwargs={"slug": self.slug})

    @property
    def full_props(self) -> str:
        if self.album and self.authors:
            return f"{self.album.name} - " + ", ".join(
                self.authors.values_list("name", flat=True)
            )
        elif self.album:
            return f"{self.album.name}"
        elif self.album:
            return ", ".join(self.authors.values_list("name", flat=True))
        return ""

    def __str__(self):
        return self.name

    class SlugMeta:
        slug_length = 10


class Playlist(ShortLinkModel, UserHistoryModel):
    name = models.CharField(max_length=200)
    private = models.BooleanField(default=False)
    creator = models.ForeignKey(
        "users.User", related_name="playlists", on_delete=models.CASCADE
    )
    length = models.IntegerField(default=0)

    def get_absolute_url(self):
        return reverse("playlist:song", kwargs={"slug": self.slug})

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
