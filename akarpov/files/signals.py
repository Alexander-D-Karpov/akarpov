from django.db.models.signals import post_save
from django.dispatch import receiver

from akarpov.files.models import File
from akarpov.files.tasks import generate_file_review


@receiver(post_save, sender=File)
def post_on_create(sender, instance: File, created, **kwargs):
    if created:
        generate_file_review.apply_async(
            kwargs={
                "pk": instance.pk,
            },
            countdown=2,
        )
