import os

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from akarpov.music.models import PlaylistSong, Song, SongUserRating


@receiver(post_delete, sender=Song)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


@receiver(post_save)
def send_que_status(sender, instance, created, **kwargs):
    ...


@receiver(pre_save, sender=SongUserRating)
def create_or_update_rating(sender, instance: SongUserRating, **kwargs):
    song = instance.song
    if instance.pk:
        previous = SongUserRating.objects.get(pk=instance.pk)
        if previous.like != instance.like:
            if instance.like:
                song.likes += 2
            else:
                song.likes -= 2
    else:
        if instance.like:
            song.likes += 1
        else:
            song.likes -= 1
    song.save(update_fields=["likes"])


@receiver(post_delete, sender=SongUserRating)
def delete_rating(sender, instance: SongUserRating, **kwargs):
    song = instance.song
    if instance.like:
        song.likes -= 1
    else:
        song.likes += 1
    song.save(update_fields=["likes"])


@receiver(post_save, sender=PlaylistSong)
def update_playlist_length(sender, instance: PlaylistSong, **kwargs):
    playlist = instance.playlist
    playlist.length = playlist.songs.count()
    playlist.save(update_fields=["length"])


@receiver(post_delete, sender=PlaylistSong)
def update_playlist_length_delete(sender, instance: PlaylistSong, **kwargs):
    playlist = instance.playlist
    playlist.length = playlist.songs.count()
    playlist.save(update_fields=["length"])
