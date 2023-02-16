from django.db import models

from akarpov.pipeliner.models import BaseBlock


class Workspace(models.Model):
    blocks: list[BaseBlock]

    name = models.CharField(max_length=50, blank=True)
    slug = models.SlugField(max_length=8)

    def __str__(self):
        return self.name
