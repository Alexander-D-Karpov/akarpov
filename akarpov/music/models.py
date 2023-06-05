from django.db import models
from django.urls import reverse

from akarpov.common.models import BaseImageModel
from akarpov.tools.shortener.models import ShortLink


class Author(BaseImageModel, ShortLink):
    name = models.CharField(max_length=200)
    link = models.URLField(blank=True)

    def get_absolute_url(self):
        return reverse("music:author", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


class Album(BaseImageModel, ShortLink):
    name = models.CharField(max_length=200)
    link = models.URLField(blank=True)

    def get_absolute_url(self):
        return reverse("music:album", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


class Song(BaseImageModel, ShortLink):
    link = models.URLField(blank=True)
    length = models.IntegerField(null=True)
    played = models.IntegerField(default=0)
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to="music")
    author = models.ForeignKey(
        Author, null=True, related_name="songs", on_delete=models.SET_NULL
    )
    album = models.ForeignKey(
        Album, null=True, related_name="songs", on_delete=models.SET_NULL
    )

    def get_absolute_url(self):
        return reverse("music:song", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name

    class SlugMeta:
        slug_length = 10


class Playlist(ShortLink):
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
    song = models.OneToOneField("Song", related_name="que", on_delete=models.CASCADE)
    name = models.CharField(blank=True, max_length=250)
    error = models.BooleanField(default=False)
