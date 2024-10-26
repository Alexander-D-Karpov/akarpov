# Generated by Django 4.2.16 on 2024-10-26 10:37

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("music", "0016_anonmusicuser_song_created_song_volume_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="MusicDraft",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("failed", "Failed"),
                            ("complete", "Complete"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "provider",
                    models.CharField(
                        choices=[
                            ("spotify", "Spotify"),
                            ("yandex", "Yandex"),
                            ("youtube", "YouTube"),
                        ],
                        max_length=20,
                    ),
                ),
                ("original_url", models.URLField()),
                ("meta_data", models.JSONField(blank=True, null=True)),
                ("file_token", models.CharField(max_length=100, unique=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("error_message", models.TextField(blank=True, null=True)),
                ("user_id", models.IntegerField(null=True)),
                (
                    "callback_token",
                    models.UUIDField(default=uuid.uuid4, editable=False),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MusicDraftFile",
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
                ("file", models.FileField(upload_to="music_drafts/")),
                ("original_name", models.CharField(max_length=255)),
                ("mime_type", models.CharField(max_length=100)),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "draft",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files",
                        to="music.musicdraft",
                    ),
                ),
            ],
        ),
    ]
