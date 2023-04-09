import os

from django.conf import settings
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

from akarpov.files.services.files import user_unique_file_upload
from akarpov.tools.shortener.models import ShortLink


class File(TimeStampedModel, ShortLink):
    """model to store user's files"""

    private = BooleanField(default=True)

    user = ForeignKey("users.User", related_name="files", on_delete=CASCADE)
    folder = ForeignKey(
        "files.Folder", related_name="files", blank=True, null=True, on_delete=CASCADE
    )

    preview = FileField(blank=True, upload_to="file/previews/")
    file = FileField(blank=False, upload_to=user_unique_file_upload)

    # meta
    name = CharField(max_length=100, null=True, blank=True)
    description = TextField(blank=True, null=True)
    file_type = CharField(max_length=50, null=True, blank=True)

    @property
    def file_image_url(self):
        if self.preview:
            return self.preview.url
        end = self.file.path.split(".")[-1]
        path = settings.STATICFILES_DIRS[0] + f"/images/files/{end}.png"
        if os.path.isfile(path):
            return settings.STATIC_URL + f"images/files/{end}.png"
        return settings.STATIC_URL + "images/files/_blank.png"

    @property
    def file_size(self):
        if self.file:
            return self.file.size
        return 0

    def get_absolute_url(self):
        return reverse("files:view", kwargs={"slug": self.slug})

    def __str__(self):
        return f"file: {self.name}"

    class Meta:
        ordering = ["-modified"]


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
