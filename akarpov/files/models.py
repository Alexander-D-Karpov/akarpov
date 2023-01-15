from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    FileField,
    ForeignKey,
    SlugField,
    TextField,
)
from model_utils.models import TimeStampedModel

from akarpov.utils.files import user_file_upload_mixin


class BaseFile(TimeStampedModel):
    """model to store user's files"""

    name = CharField(max_length=100)
    description = TextField()

    slug = SlugField(max_length=20, blank=True)
    private = BooleanField(default=True)

    user = ForeignKey("users.User", related_name="files", on_delete=CASCADE)
    folder = ForeignKey(
        "files.Folder", related_name="files", null=True, on_delete=CASCADE
    )

    file = FileField(blank=False, upload_to=user_file_upload_mixin)

    def __str__(self):
        return f"file: {self.name}"


class Folder(TimeStampedModel):
    name = CharField(max_length=100)
    slug = SlugField(max_length=20, blank=True)

    user = ForeignKey("users.User", related_name="files_folders", on_delete=CASCADE)
    parent = ForeignKey("self", related_name="children", on_delete=CASCADE)

    def __str__(self):
        return f"file: {self.name}"
