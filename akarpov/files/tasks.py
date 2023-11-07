import os
import time

import structlog
from celery import shared_task
from django.core.files import File
from haystack.management.commands import rebuild_index, update_index
from haystack.query import SearchQuerySet

from akarpov.files.models import File as FileModel
from akarpov.files.services.preview import create_preview, get_file_mimetype
from akarpov.files.services.text import extract_file_text

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
    file.content = extract_file_text(file.file.path)
    file.save(update_fields=["preview", "name", "file_type", "content"])
    if pth and os.path.isfile(pth):
        os.remove(pth)
    return pk


@shared_task
def task_rebuild_index():
    start_time = time.time()
    rebuild_index.Command().handle(interactive=False)
    end_time = time.time()
    duration = end_time - start_time

    indexed_count = SearchQuerySet().all().count()

    logger.info(
        "index_rebuild_finished", duration=duration, indexed_count=indexed_count
    )


@shared_task
def update_index_task():
    start_time = time.time()

    update_index.Command().handle(interactive=False)
    end_time = time.time()
    duration = end_time - start_time
    logger.info("update_index_completed", duration=duration)
