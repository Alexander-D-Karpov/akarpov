from decimal import Decimal as D
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from faker.providers.python import Provider as PythonProvider
from PIL import Image


class MoneyProvider(PythonProvider):
    def money(self):
        return self.pydecimal(right_digits=2, min_value=D(1), max_value=D(1000))


additional_providers = [MoneyProvider]


def configure_factory_faker(factory_faker):
    factory_faker._DEFAULT_LOCALE = "ru_RU"
    for provider in additional_providers:
        factory_faker.add_provider(provider, locale="ru_RU")


def configure_faker(faker):
    for provider in additional_providers:
        faker.add_provider(provider)


def django_image(name, size=200, color="red"):
    thumb = Image.new(
        "RGB",
        (
            size,
            size,
        ),
        color,
    )
    thumb_io = BytesIO()
    thumb.save(thumb_io, format="JPEG")
    thumb_io.seek(0)
    return InMemoryUploadedFile(
        thumb_io, None, name, "image/jpeg", thumb_io.getbuffer().nbytes, None
    )
