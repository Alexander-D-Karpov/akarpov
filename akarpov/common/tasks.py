from celery import shared_task
from django.apps import apps
from django.core.files import File

from akarpov.utils.files import crop_image


@shared_task()
def crop_model_image(pk: int, app_label: str, model_name: str):
    model = apps.get_model(app_label=app_label, model_name=model_name)
    instance = model.objects.get(pk=pk)
    instance.image_cropped.save(
        instance.image.path.split(".")[0].split("/")[-1] + ".png",
        File(crop_image(instance.image.path, length=250)),
        save=False,
    )
    instance.save(update_fields=["image_cropped"])
    return pk
