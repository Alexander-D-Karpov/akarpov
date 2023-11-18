from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from location_field.models.plain import PlainLocationField

from akarpov.common.models import BaseImageModel
from akarpov.tools.shortener.models import ShortLinkModel
from akarpov.users.services.history import UserHistoryModel
from akarpov.utils.files import user_file_upload_mixin


class Collection(TimeStampedModel, ShortLinkModel, UserHistoryModel):
    name = models.CharField(max_length=250, blank=True)
    description = models.TextField()
    public = models.BooleanField(default=False)
    user = models.ForeignKey(
        "users.User", related_name="collections", on_delete=models.CASCADE
    )

    def get_absolute_url(self):
        return reverse("gallery:collection", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Collection"


class Image(TimeStampedModel, ShortLinkModel, BaseImageModel, UserHistoryModel):
    collection = models.ForeignKey(
        "Collection", related_name="images", on_delete=models.CASCADE
    )
    public = models.BooleanField(default=False)
    user = models.ForeignKey(
        "users.User", related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=user_file_upload_mixin, blank=False, null=False)
    tags = models.ManyToManyField("Tag", related_name="images")

    # image meta
    extra_data = models.JSONField(default=dict)
    image_city = models.CharField(max_length=255, null=True, blank=True)
    image_location = PlainLocationField(
        based_fields=["image_city"], zoom=7, null=True, blank=True
    )

    def get_absolute_url(self):
        return reverse("gallery:view", kwargs={"slug": self.slug})

    def __str__(self):
        return self.image.name

    class Meta:
        verbose_name = "Image"


class Tag(ShortLinkModel):
    name = models.CharField(max_length=255, null=True, blank=True)

    def get_absolute_url(self):
        return reverse("gallery:tag", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name
