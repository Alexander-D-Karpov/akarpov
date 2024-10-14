import base64
import time
from urllib.parse import urljoin

import requests
import structlog
from celery import shared_task
from django.conf import settings
from django.core import management
from django.core.files.base import ContentFile

from akarpov.files.models import File as FileModel

logger = structlog.get_logger(__name__)


def sanitize_content(content):
    """Remove NUL (0x00) characters from the content."""
    if isinstance(content, str):
        return content.replace("\x00", "")
    elif isinstance(content, bytes):
        return content.replace(b"\x00", b"")
    return content


@shared_task()
def process_file(pk: int):
    file = FileModel.objects.get(pk=pk)
    if not file.name:
        file.name = file.file.name.split("/")[-1]

    try:
        api_url = urljoin(settings.PREVIEW_SERVICE_URL, "/process_file/")

        files = {"file": (file.name, file.file.open("rb"))}
        headers = {
            "X-API-Key": settings.PREVIEW_SERVICE_API_KEY,
            "Accept": "application/json",
        }

        response = requests.post(api_url, files=files, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to process file {pk}: {response.text}")
            return

        result = response.json()

        file.file_type = result["file_type"]
        file.content = sanitize_content(result["content"])

        if result["preview"]:
            image_data = base64.b64decode(result["preview"])
            file.preview.save(
                f"{file.name}_preview.jpg", ContentFile(image_data), save=False
            )

        file.save()

        logger.info(f"File {pk} processed successfully")

    except Exception as e:
        logger.error(f"Error processing file {pk}: {str(e)}")
    finally:
        file.file.close()

    return pk


@shared_task
def update_index_task():
    start_time = time.time()
    management.call_command("search_index", "--rebuild", "-f")
    end_time = time.time()
    duration = end_time - start_time
    logger.info("update_index_completed", duration=duration)
