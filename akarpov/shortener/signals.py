from django.db.models.signals import post_save
from django.dispatch import receiver

from akarpov.shortener.models import Link
from akarpov.shortener.services import generate_slug


@receiver(post_save, sender=Link)
def link_on_create(sender, instance: Link, created, **kwargs):
    if created:
        instance.slug = generate_slug(instance.id)
        instance.save(update_fields=["slug"])
