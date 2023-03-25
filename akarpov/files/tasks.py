from celery import shared_task
from django.core.files import File

from akarpov.files.models import File as FileModel
from akarpov.files.services.preview import create_preview


@shared_task()
def generate_file_review(pk: int):
    file = FileModel.objects.get(pk=pk)
    pth = create_preview(file.file)
    with open(pth, "rb") as f:
        file.preview.save(
            pth.split("/")[-1],
            File(f.read()),
            save=False,
        )
    file.save(update_fields=["preview"])
    return pk
