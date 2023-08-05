# Generated by Django 4.2.3 on 2023-07-09 19:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("music", "0003_remove_song_author_remove_songinque_song_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="RadioSong",
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
                ("slug", models.SlugField(unique=True)),
                (
                    "song",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="radio",
                        to="music.song",
                    ),
                ),
            ],
        ),
    ]