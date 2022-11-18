from django.contrib.auth.models import AbstractUser
from django.db import models

from akarpov.utils.files import user_file_upload_mixin


class User(AbstractUser):
    """Base user model, to store all user info"""

    first_name = None
    last_name = None

    image = models.ImageField(upload_to=user_file_upload_mixin, blank=True)
    image_cropped = models.ImageField(upload_to="cropped/", blank=True)

    about = models.TextField(blank=True)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ["-id"]
