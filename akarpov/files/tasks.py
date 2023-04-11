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
    pth = None
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
    file.file_type = get_file_mimetype(file.file.path)
    descr = None
    try:
        descr = get_description(file.file.path)
        if descr:
            with open(descr, encoding="utf-8") as f:
                data = f.read()
                file.description = data
    except Exception as e:
        logger.error(e)
    file.save(update_fields=["preview", "name", "file_type", "description"])
    if pth and os.path.isfile(pth):
        os.remove(pth)
    if descr and os.path.isfile(descr):
        os.remove(descr)
    return pk
