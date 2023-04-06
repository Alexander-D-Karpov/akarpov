from django.db.models.signals import post_save
from django.dispatch import receiver

from akarpov.files.models import File
from akarpov.files.tasks import process_file


@receiver(post_save, sender=File)
def post_on_create(sender, instance: File, created, **kwargs):
    if created:
        process_file.apply_async(
            kwargs={
                "pk": instance.pk,
            },
            countdown=2,
        )
