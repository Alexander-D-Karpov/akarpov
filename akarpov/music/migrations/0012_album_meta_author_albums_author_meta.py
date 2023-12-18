# Generated by Django 4.2.8 on 2023-12-17 22:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("music", "0011_alter_playlist_private_userlistenhistory"),
    ]

    operations = [
        migrations.AddField(
            model_name="album",
            name="meta",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="author",
            name="albums",
            field=models.ManyToManyField(related_name="authors", to="music.album"),
        ),
        migrations.AddField(
            model_name="author",
            name="meta",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
