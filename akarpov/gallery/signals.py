from django.db.models.signals import post_save
from django.dispatch import receiver

from akarpov.gallery.models import Image
from akarpov.gallery.tasks import process_gallery_image


@receiver(post_save, sender=Image)
def image_create(sender, instance: Image, created, **kwargs):
    if created:
        process_gallery_image.apply_async(
            kwargs={
                "pk": instance.pk,
            },
            countdown=2,
        )
