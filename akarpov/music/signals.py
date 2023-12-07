import os

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from akarpov.music.models import Song, SongUserRating


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
