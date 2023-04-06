import os

from celery import shared_task
from django.core.files import File

from akarpov.files.models import File as FileModel
from akarpov.files.services.preview import create_preview


@shared_task()
def process_file(pk: int):
    file = FileModel.objects.get(pk=pk)
    if not file.name:
        file.name = file.file.name
    pth = create_preview(file.file)
    with open(pth, "rb") as f:
        file.preview.save(
            pth.split("/")[-1],
            File(f),
            save=False,
        )
    file.save(update_fields=["preview"])
    if os.path.isfile(pth):
        os.remove(pth)
    return pk
