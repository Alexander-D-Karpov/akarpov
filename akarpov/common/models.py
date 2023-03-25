import os

from django.db import models

from akarpov.common.tasks import crop_model_image
from akarpov.utils.files import user_file_upload_mixin
from akarpov.utils.generators import generate_charset


def create_cropped_model_image(sender, instance, created, **kwargs):
    model = sender
    if created:
        if instance.image:
            crop_model_image.apply_async(
                kwargs={
                    "pk": instance.pk,
                    "app_label": model._meta.app_label,
                    "model_name": model._meta.model_name,
                },
                countdown=2,
            )


def update_cropped_model_image(sender, instance, **kwargs):
    model = sender
    if instance.id:
        previous = model.objects.get(id=instance.id)
        if previous.image != instance.image:
            # delete previous cropped image
            if instance.image_cropped:
                if os.path.isfile(instance.image_cropped.path):
                    os.remove(instance.image_cropped.path)
            # run task to create new cropped image
            if kwargs["update_fields"] != frozenset({"image_cropped"}) and instance:
                if instance.image:
                    crop_model_image.apply_async(
                        kwargs={
                            "pk": instance.pk,
                            "app_label": model._meta.app_label,
                            "model_name": model._meta.model_name,
                        },
                        countdown=2,
                    )
                else:
                    instance.image_cropped = None


def delete_cropped_model_image(sender, instance, **kwargs):
    print(instance.image_cropped)
    if instance.image_cropped:
        if os.path.isfile(instance.image_cropped.path):
            os.remove(instance.image_cropped.path)


class BaseImageModel(models.Model):
    """
    stores user's images in their media folder, creates, updates and deletes preview
    requires celery to run
    """

    image = models.ImageField(upload_to=user_file_upload_mixin, blank=True)
    image_cropped = models.ImageField(upload_to="cropped/", blank=True)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        models.signals.pre_save.connect(update_cropped_model_image, sender=cls)
        models.signals.post_save.connect(create_cropped_model_image, sender=cls)
        models.signals.post_delete.connect(delete_cropped_model_image, sender=cls)

    class Meta:
        abstract = True


def create_model_slug(sender, instance, **kwargs):
    def _generate_charset():
        if private:
            return generate_charset(private_slug_length)
        return generate_charset(slug_length)

    if instance.id is None:
        model = sender
        slug_length = 5
        private_slug_length = 20
        private = False

        if hasattr(model, "SlugMeta"):
            if hasattr(model.SlugMeta, "slug_length"):
                slug_length = model.SlugMeta.slug_length
            if hasattr(model.SlugMeta, "private_slug_length"):
                private_slug_length = model.SlugMeta.private_slug_length
        if hasattr(instance, "private"):
            if instance.private:
                private = True
        if hasattr(instance, "public"):
            if not instance.public:
                private = True

        slug = _generate_charset()
        while model.objects.filter(slug=slug).exists():
            slug = _generate_charset()
        instance.slug = slug


class SlugModel(models.Model):
    """
    model to store and generate slug for model instances
    for custom slug length use: slug_length, private_slug_length Meta options
    """

    slug = models.SlugField(max_length=20, blank=True, unique=True)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        models.signals.pre_save.connect(create_model_slug, sender=cls)

    class Meta:
        abstract = True

    class SlugMeta:
        slug_length = 5
        private_slug_length = 20
