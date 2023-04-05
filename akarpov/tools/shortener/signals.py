from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from akarpov.tools.shortener.models import Link
from akarpov.utils.generators import generate_charset, get_str_uuid

if hasattr(settings, "SHORTENER_SLUG_LENGTH"):
    length = settings.SHORTENER_SLUG_LENGTH
else:
    length = 0


def generate_slug(pk: int) -> str:
    if settings.SHORTENER_ADD_SLUG:
        slug = generate_charset(length)
        return slug + get_str_uuid(pk)
    return get_str_uuid(pk)


@receiver(post_save, sender=Link)
def link_on_create(sender, instance, created, **kwargs):
    if created:
        instance.slug = generate_slug(instance.id)
        instance.save(update_fields=["slug"])
