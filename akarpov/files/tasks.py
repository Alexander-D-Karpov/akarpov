import os

import structlog
from celery import shared_task
from django.core.files import File

from akarpov.files.models import File as FileModel
from akarpov.files.services.preview import (
    create_preview,
    get_description,
    get_file_mimetype,
)

logger = structlog.get_logger(__name__)


@shared_task()
def process_file(pk: int):
    file = FileModel.objects.get(pk=pk)
    if not file.name:
        file.name = file.file.name.split("/")[-1]
    try:
        pth = create_preview(file.file.path)
        if pth:
            with open(pth, "rb") as f:
                file.preview.save(
                    pth.split("/")[-1],
                    File(f),
                    save=False,
                )
    except Exception as e:
        logger.error(e)
    file.type = get_file_mimetype(file.file.path)
    file.description = get_description(file.file.path)
    file.save(update_fields=["preview", "name", "file_type", "description"])
    if pth and os.path.isfile(pth):
        os.remove(pth)
    return pk
