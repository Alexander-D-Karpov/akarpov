from django.db.models.signals import pre_save
from django.dispatch import receiver

from akarpov.files.models import BaseFile
from akarpov.utils.generators import generate_charset


@receiver(pre_save, sender=BaseFile)
def file_on_save(sender, instance: BaseFile, **kwargs):
    if instance.id is None:
        if instance.private:
            slug = generate_charset(20)
            while BaseFile.objects.filter(slug=slug).exists():
                slug = generate_charset(20)
        else:
            slug = generate_charset(5)
            while BaseFile.objects.filter(slug=slug).exists():
                slug = generate_charset(5)

        instance.slug = slug
