from django.db import models

from akarpov.pipeliner.models import ProviderBlock


class ConstantNumberBlock(ProviderBlock):
    TYPE = "Number"

    number = models.DecimalField(max_digits=5, decimal_places=2)


class ConstantStringBlock(ProviderBlock):
    TYPE = "String"

    string = models.TextField()
