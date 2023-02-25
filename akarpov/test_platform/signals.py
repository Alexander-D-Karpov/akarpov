from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from akarpov.common.tasks import crop_model_image
from akarpov.test_platform.models import Form
from akarpov.utils.generators import generate_charset


@receiver(post_save, sender=Form)
def form_on_create(sender, instance: Form, created, **kwargs):
    if created:
        if instance.image:
            crop_model_image.apply_async(
                kwargs={
                    "pk": instance.pk,
                    "app_label": "test_platform",
                    "model_name": "Form",
                },
                countdown=2,
            )


@receiver(pre_save, sender=Form)
def form_on_save(sender, instance: Form, **kwargs):
    if instance.id is None:
        if instance.public:
            slug = generate_charset(5)
            while Form.objects.filter(slug=slug).exists():
                slug = generate_charset(5)
            instance.slug = slug
        else:
            slug = generate_charset(20)
            while Form.objects.filter(slug=slug).exists():
                slug = generate_charset(20)
            instance.slug = slug
    else:
        previous = Form.objects.get(id=instance.id)
        if (
            previous.image != instance.image
            and kwargs["update_fields"] != frozenset({"image_cropped"})
            and instance
        ):
            if instance.image:
                crop_model_image.apply_async(
                    kwargs={
                        "pk": instance.pk,
                        "app_label": "test_platform",
                        "model_name": "Form",
                    },
                    countdown=2,
                )
            else:
                instance.image_cropped = None
