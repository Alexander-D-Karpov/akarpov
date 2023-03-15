from django.db import models

from akarpov.utils.files import user_file_upload_mixin


class BaseImageModel(models.Model):
    image = models.ImageField(upload_to=user_file_upload_mixin, blank=True)
    image_cropped = models.ImageField(upload_to="cropped/", blank=True)

    class Meta:
        abstract = True
