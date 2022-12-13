from django.db import models

from akarpov.pipeliner.models import BaseBlock


class MultiplicationBlock(BaseBlock):
    TYPE = "Multiply"

    by = models.DecimalField(max_digits=5, decimal_places=2)
