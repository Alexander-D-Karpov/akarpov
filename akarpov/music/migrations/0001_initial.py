# Generated by Django 4.2.1 on 2023-06-05 19:01

import akarpov.utils.files
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("shortener", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Album",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True, upload_to=akarpov.utils.files.user_file_upload_mixin
                    ),
                ),
                ("image_cropped", models.ImageField(blank=True, upload_to="cropped/")),
                ("slug", models.SlugField(blank=True, max_length=20, unique=True)),
                ("name", models.CharField(max_length=200)),
                ("link", models.URLField(blank=True)),
                (
                    "short_link",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="shortener.link",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Author",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True, upload_to=akarpov.utils.files.user_file_upload_mixin
                    ),
                ),
                ("image_cropped", models.ImageField(blank=True, upload_to="cropped/")),
                ("slug", models.SlugField(blank=True, max_length=20, unique=True)),
                ("name", models.CharField(max_length=200)),
                ("link", models.URLField(blank=True)),
                (
                    "short_link",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="shortener.link",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Playlist",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("slug", models.SlugField(blank=True, max_length=20, unique=True)),
                ("name", models.CharField(max_length=200)),
                ("private", models.BooleanField(default=False)),
                ("length", models.IntegerField(default=0)),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="playlists",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "short_link",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="shortener.link",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Song",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True, upload_to=akarpov.utils.files.user_file_upload_mixin
                    ),
                ),
                ("image_cropped", models.ImageField(blank=True, upload_to="cropped/")),
                ("slug", models.SlugField(blank=True, max_length=20, unique=True)),
                ("link", models.URLField(blank=True)),
                ("length", models.IntegerField(null=True)),
                ("played", models.IntegerField(default=0)),
                ("name", models.CharField(max_length=200)),
                ("file", models.FileField(upload_to="music")),
                (
                    "album",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="songs",
                        to="music.album",
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="songs",
                        to="music.author",
                    ),
                ),
                (
                    "short_link",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="shortener.link",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SongInQue",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=250)),
                ("error", models.BooleanField(default=False)),
                (
                    "song",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="que",
                        to="music.song",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PlaylistSong",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("order", models.IntegerField()),
                (
                    "playlist",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="songs",
                        to="music.playlist",
                    ),
                ),
                (
                    "song",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="playlists",
                        to="music.song",
                    ),
                ),
            ],
            options={
                "ordering": ["order"],
                "unique_together": {("playlist", "order"), ("playlist", "song")},
            },
        ),
    ]
