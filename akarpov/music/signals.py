import os

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from akarpov.music.models import Album, Author, PlaylistSong, Song, SongUserRating
from akarpov.music.services.file import set_song_volume
from akarpov.music.services.info import update_album_info, update_author_info


@receiver(post_delete, sender=Song)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


@receiver(post_save, sender=Song)
def song_create(sender, instance: Song, created, **kwargs):
    if instance.volume is None and instance.file:
        set_song_volume(instance)


@receiver(post_save, sender=Author)
def author_create(sender, instance, created, **kwargs):
    if created:
        update_author_info(instance)


@receiver(post_save, sender=Album)
def album_create(sender, instance, created, **kwargs):
    if created:
        authors = instance.authors.all()
        update_album_info(instance, authors.first().name if authors.exists() else None)


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
