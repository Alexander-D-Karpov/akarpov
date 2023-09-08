import io
import logging
import re

import factory
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from pytest_django.lazy_django import skip_if_no_django
from rest_framework.test import APIClient

from akarpov.utils.config import build_redis_uri
from akarpov.utils.faker import configure_factory_faker, configure_faker
from akarpov.utils.pytest_factoryboy import autodiscover_factories

configure_factory_faker(factory.Faker)

autodiscover_factories()

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def activate_django_db(db):
    pass


@pytest.fixture(scope="session", autouse=True)
def update_config():
    from django.conf import settings

    settings.DEBUG = True


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_client(client, user_factory):
    admin_user = user_factory(is_superuser=True, is_staff=True)
    client.force_login(admin_user)
    return client


@pytest.fixture
def api_user_client(api_client, user):
    api_client.force_authenticate(user)
    return api_client


@pytest.fixture
def image_factory():
    def factory(filename="test.jpg", **params):
        from PIL import Image

        width = params.get("width", 520)
        height = params.get("height", width)
        color = params.get("color", "blue")
        image_format = params.get("format", "JPEG")
        image_palette = params.get("palette", "RGB")

        thumb_io = io.BytesIO()
        with Image.new(image_palette, (width, height), color) as thumb:
            thumb.save(thumb_io, format=image_format)
        return SimpleUploadedFile(filename, thumb_io.getvalue())

    return factory


@pytest.fixture
def image(image_factory):
    return image_factory()


@pytest.fixture
def uploaded_photo(image):
    return SimpleUploadedFile("test.png", image.read())


@pytest.fixture
def plain_file():
    return io.BytesIO(b"plain_text")


@pytest.fixture(scope="session", autouse=True)
def faker_session_locale():
    return ["en"]


@pytest.fixture(autouse=True)
def add_faker_providers(faker):
    configure_faker(faker)
    return faker


@pytest.fixture(scope="session", autouse=True)
def set_test_redis_databases(request):
    from django.conf import settings

    skip_if_no_django()
    xdist_worker = getattr(request.config, "workerinput", {}).get("workerid")
    if xdist_worker is None:
        return
    worker_number_search = re.search(r"\d+", xdist_worker)
    if not worker_number_search:
        return
    max_db_number = worker_number_search[0]
    max_db_number = int(max_db_number) * 3 + 2
    channels_redis_url = build_redis_uri(
        settings.CHANNELS_REDIS_HOST,
        settings.CHANNELS_REDIS_PORT,
        settings.CHANNELS_REDIS_USER,
        settings.CHANNELS_REDIS_PASSWORD,
        max_db_number,
    )
    settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0][
        "address"
    ] = channels_redis_url
    settings.CHANNELS_REDIS_DB = max_db_number
    settings.CLICKHOUSE_REDIS_CONFIG["db"] = max_db_number - 1
    settings.CELERY_REDIS_DB = max_db_number - 2
