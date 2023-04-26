import os

from django.core.files.base import File
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.timezone import now

from akarpov.files.models import File as FileModel
from akarpov.files.models import FileInTrash
from akarpov.files.tasks import process_file


@receiver(post_save, sender=FileModel)
def file_on_create(sender, instance: FileModel, created, **kwargs):
    if created:
        for folder in instance.get_top_folders():
            folder.modified = now()
            folder.size += instance.file_size
            folder.amount += 1
            folder.save()
        process_file.apply_async(
            kwargs={
                "pk": instance.pk,
            },
            countdown=2,
        )


@receiver(post_delete, sender=FileModel)
def move_file_to_trash(sender, instance, **kwargs):
    if instance.file:
        file_size = 0
        path = instance.file.path
        file_dir = "/".join(path.split("/")[:-1]) + "/"

        if os.path.isfile(path):
            file_size = instance.file.size

        for folder in instance.get_top_folders():
            folder.modified = now()
            folder.size -= file_size
            folder.amount -= 1
            folder.save()

        if os.path.isfile(path):
            name = instance.file.name.split("/")[-1]
            trash = FileInTrash(user=instance.user, name=name)
            trash.file = File(instance.file, name=name)
            trash.save()

        if os.path.isfile(path):
            os.remove(path)
            if os.path.isdir(file_dir) and len(os.listdir(file_dir)) == 0:
                os.rmdir(file_dir)


@receiver(post_delete, sender=FileInTrash)
def trunk_deleted_file(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
