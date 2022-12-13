from django.db import models

from akarpov.pipeliner.models import BaseBlock


class TrashBlock(BaseBlock):
    TYPE = "Trash"

    storage = models.ForeignKey("Storage", on_delete=models.CASCADE)
