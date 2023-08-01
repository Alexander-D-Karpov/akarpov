import uuid

from django.db import models
from model_utils.models import TimeStampedModel

from akarpov.tools.shortener.models import ShortLinkModel
from akarpov.users.services.history import UserHistoryModel


class WorkSpace(TimeStampedModel, ShortLinkModel, UserHistoryModel):
    name = models.CharField(default="WorkSpace", max_length=200)
    creator = models.ForeignKey(
        "users.User", related_name="workspaces", on_delete=models.CASCADE
    )
    private = models.BooleanField(default=True)


class Block(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        "WorkSpace", related_name="blocks", on_delete=models.CASCADE
    )
    parents = models.ForeignKey(
        "self", related_name="children", on_delete=models.CASCADE
    )

    type = models.CharField(max_length=250, db_index=True)
    context = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"block {self.id} - {self.type}"
