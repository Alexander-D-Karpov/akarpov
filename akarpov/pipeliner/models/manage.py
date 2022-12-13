from django.db import models


class Workspace(models.Model):
    name = models.CharField(max_length=50, blank=True)
    slug = models.SlugField(max_length=8)

    def __str__(self):
        return self.name
