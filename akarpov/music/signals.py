import os

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from akarpov.music.models import Song


@receiver(post_delete, sender=Song)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


@receiver(post_save)
def send_que_status(sender, instance, created, **kwargs):
    ...
