import os

from akarpov.common.tasks import crop_model_image


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
                countdown=5,
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
    if instance.image_cropped:
        if os.path.isfile(instance.image_cropped.path):
            os.remove(instance.image_cropped.path)
