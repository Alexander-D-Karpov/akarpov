from collections.abc import Sequence
from typing import Any

from django.contrib.auth import get_user_model
from factory import Faker, post_generation
from factory.django import DjangoModelFactory

from akarpov.utils.faker import django_image


class UserFactory(DjangoModelFactory):
    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")
    about = Faker("text")

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    @post_generation
    def image(self, create, extracted, **kwargs):
        if extracted:
            image_name, image = extracted
        else:
            image_name = "test.jpg"
            image = django_image(image_name, **kwargs)
        self.image.save(image_name, image)

    class Meta:
        model = get_user_model()
        skip_postgeneration_save = False
        django_get_or_create = ["username"]
