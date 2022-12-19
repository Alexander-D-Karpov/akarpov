import uuid

from django.db import models
from polymorphic.models import PolymorphicModel


class BaseBlock(PolymorphicModel):
    """Base block for pipelines for further explanation check examples"""

    TYPE = "Base"

    name: models.CharField
    created: models.DateTimeField
    updated: models.DateTimeField

    creator: models.ForeignKey
    workspace: models.ForeignKey
    parent: models.ForeignKey

    name = models.CharField(max_length=100, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    creator = models.ForeignKey(
        "users.User", related_name="pipeline_blocks", on_delete=models.CASCADE
    )
    workspace = models.ForeignKey(
        "Workspace", related_name="blocks", on_delete=models.CASCADE
    )
    parent = models.ForeignKey(
        "self", null=True, related_name="children", on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.TYPE} block"


class ProviderBlock(BaseBlock):
    TYPE = "Provider"
    parent = None

    class Meta:
        abstract = True


class BaseStorage(PolymorphicModel):
    id: uuid.uuid4 = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )


class Storage(BaseStorage):
    data = models.JSONField(default=dict)


class RunnerStorage(BaseStorage):
    data = models.JSONField(default=dict)
