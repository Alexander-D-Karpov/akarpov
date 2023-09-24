import os

from django.conf import settings
from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateTimeField,
    FileField,
    ForeignKey,
    IntegerField,
    Model,
    Q,
    SlugField,
    TextField,
)
from django.urls import reverse
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from model_utils.models import TimeStampedModel
from polymorphic.models import PolymorphicModel

from akarpov.files.services.files import trash_file_upload, user_unique_file_upload
from akarpov.tools.shortener.models import ShortLinkModel
from akarpov.users.services.history import UserHistoryModel


class BaseFileItem(PolymorphicModel):
    parent = ForeignKey(
        verbose_name="Folder",
        to="files.Folder",
        null=True,
        blank=True,
        on_delete=CASCADE,
        related_name="children",
    )
    user = ForeignKey("users.User", related_name="files", on_delete=CASCADE)
    created = AutoCreatedField("created")
    modified = AutoLastModifiedField("updated")

    views = IntegerField(default=0)
    downloads = IntegerField(default=0)

    class Meta:
        ordering = ["-modified"]

    @property
    def is_file(self):
        return type(self) is File

    def get_top_folders(self):
        folders = []
        obj = self
        while obj.parent:
            folders.append(obj.parent)
            obj = obj.parent
        return folders[::-1]

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields", None)
        if update_fields:
            kwargs["update_fields"] = set(update_fields).union({"modified"})
        super().save(*args, **kwargs)


class File(BaseFileItem, TimeStampedModel, ShortLinkModel, UserHistoryModel):
    """model to store user's files"""

    private = BooleanField(default=True)

    preview = FileField(blank=True, upload_to="file/previews/")
    file_obj = FileField(blank=False, upload_to=user_unique_file_upload)

    # meta
    name = CharField(max_length=255, null=True, blank=True)
    description = TextField(blank=True, null=True)
    file_type = CharField(max_length=255, null=True, blank=True)

    # extra settings
    notify_user_on_view = BooleanField(
        "Receive notifications on file view", default=False
    )

    @property
    def file_name(self):
        return self.file.path.split("/")[-1]

    @property
    def file(self):
        return self.file_obj

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
        verbose_name = "File"


class Folder(BaseFileItem, ShortLinkModel, UserHistoryModel):
    name = CharField(max_length=100)
    slug = SlugField(max_length=20, blank=True)
    private = BooleanField(default=True)

    # meta
    size = IntegerField(default=0)
    amount = IntegerField(default=0)

    def get_last_preview_files(self, cut=4):
        return self.children.filter(~Q(File___preview=""))[:cut]

    def get_absolute_url(self):
        return reverse("files:folder", kwargs={"slug": self.slug})

    def __str__(self):
        return f"folder: {self.name}"

    class Meta:
        verbose_name = "Folder"


class FileInTrash(TimeStampedModel):
    name = CharField(max_length=200, blank=True)
    user = ForeignKey("users.User", related_name="trash_files", on_delete=CASCADE)
    file = FileField(blank=False, upload_to=trash_file_upload)

    def __str__(self):
        return self.name


class FileReport(Model):
    created = DateTimeField(auto_now_add=True)
    file = ForeignKey("files.File", related_name="reports", on_delete=CASCADE)

    class Meta:
        verbose_name = "File report"

    def get_absolute_url(self):
        return self.file.get_absolute_url()

    def __str__(self):
        return f"report on {self.file}"
