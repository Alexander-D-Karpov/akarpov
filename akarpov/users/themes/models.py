from colorfield.fields import ColorField
from django.db import models


class Theme(models.Model):
    name = models.CharField(max_length=250)
    file = models.FileField(upload_to="themes/")
    color = ColorField()

    def __str__(self):
        return self.name
