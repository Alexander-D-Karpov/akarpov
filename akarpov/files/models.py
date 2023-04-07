from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    FileField,
    ForeignKey,
    SlugField,
    TextField,
)
from django.urls import reverse
from model_utils.models import TimeStampedModel

from akarpov.tools.shortener.models import ShortLink
from akarpov.utils.files import user_file_upload_mixin


class File(TimeStampedModel, ShortLink):
    """model to store user's files"""

    private = BooleanField(default=True)

    user = ForeignKey("users.User", related_name="files", on_delete=CASCADE)
    folder = ForeignKey(
        "files.Folder", related_name="files", blank=True, null=True, on_delete=CASCADE
    )

    preview = FileField(blank=True, upload_to="file/previews/")
    file = FileField(blank=False, upload_to=user_file_upload_mixin)

    # meta
    name = CharField(max_length=100, null=True, blank=True)
    description = TextField(blank=True, null=True)
    file_type = CharField(max_length=50, null=True, blank=True)

    def get_absolute_url(self):
        return reverse("files:view", kwargs={"slug": self.slug})

    def __str__(self):
        return f"file: {self.name}"

    class Meta:
        ordering = ["modified"]


class FileInTrash(TimeStampedModel):
    user = ForeignKey("users.User", related_name="trash_files", on_delete=CASCADE)
    file = FileField(blank=False, upload_to="file/trash/")


class Folder(TimeStampedModel, ShortLink):
    name = CharField(max_length=100)
    slug = SlugField(max_length=20, blank=True)

    user = ForeignKey("users.User", related_name="files_folders", on_delete=CASCADE)
    parent = ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=CASCADE
    )

    def get_absolute_url(self):
        return reverse("files:folder", kwargs={"slug": self.slug})

    def __str__(self):
        return f"file: {self.name}"
