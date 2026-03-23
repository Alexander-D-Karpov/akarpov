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

    @property
    def safe_length(self):
        return self.length if self.length and self.length > 0 else 300

    def get_first_author_name(self):
        if self.authors:
            return self.authors.first().name
        return ""

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


class DownloadConfig(models.Model):
    name = models.CharField(max_length=200)
    spotify_client_id = models.CharField(max_length=200, blank=True)
    spotify_client_secret = models.CharField(max_length=200, blank=True)
    proxy_url = models.CharField(max_length=500, blank=True)
    youtube_cookies = models.TextField(
        blank=True, help_text="Netscape cookie file content"
    )
    soundcloud_client_id = models.CharField(max_length=200, blank=True)
    is_default = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey("users.User", null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        default_tag = " [default]" if self.is_default else ""
        return f"{self.name}{default_tag}"

    def save(self, *args, **kwargs):
        if self.is_default:
            DownloadConfig.objects.filter(is_default=True).exclude(pk=self.pk).update(
                is_default=False
            )
        super().save(*args, **kwargs)

    @classmethod
    def get_default(cls):
        return cls.objects.filter(is_default=True).first()


class DownloadJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        RESOLVING = "resolving"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"
        RATE_LIMITED = "rate_limited"

    class Source(models.TextChoices):
        SPOTIFY = "spotify"
        YOUTUBE = "youtube"
        YANDEX = "yandex"
        SOUNDCLOUD = "soundcloud"
        UNKNOWN = "unknown"

    url = models.CharField(max_length=500)
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.UNKNOWN
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    creator = models.ForeignKey(
        "users.User", related_name="download_jobs", on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    error = models.TextField(blank=True)
    total_tracks = models.IntegerField(default=0)
    processed_tracks = models.IntegerField(default=0)
    celery_task_id = models.CharField(max_length=255, blank=True)
    config = models.ForeignKey(
        "DownloadConfig", null=True, blank=True, on_delete=models.SET_NULL
    )
    playlist_name = models.CharField(max_length=500, blank=True)
    created_playlist = models.ForeignKey(
        "Playlist", null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"[{self.source}] {self.url[:60]} ({self.status})"


class DownloadTrack(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        SEARCHING = "searching"
        DOWNLOADING = "downloading"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"
        RATE_LIMITED = "rate_limited"
        SKIPPED = "skipped"

    job = models.ForeignKey(
        DownloadJob, related_name="tracks", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=500, blank=True)
    artist_name = models.CharField(max_length=500, blank=True)
    album_name = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    error = models.TextField(blank=True)
    song = models.ForeignKey(Song, null=True, blank=True, on_delete=models.SET_NULL)
    spotify_url = models.URLField(blank=True, max_length=500)
    youtube_url = models.URLField(blank=True, max_length=500)
    duration_ms = models.IntegerField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created"]

    def __str__(self):
        return f"{self.artist_name} - {self.name} ({self.status})"


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
