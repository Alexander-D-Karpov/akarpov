import secrets

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from akarpov.common.models import BaseImageModel
from akarpov.tools.shortener.models import ShortLinkModel
from akarpov.users.themes.models import Theme


class User(AbstractUser, BaseImageModel, ShortLinkModel):
    """
    Default custom user model for akarpov.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    #: First and last name do not cover name patterns around the globe
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    about = models.TextField(_("Description"), blank=True, max_length=100)
    first_name = None  # type: ignore
    last_name = None  # type: ignore

    # files
    left_file_upload = models.BigIntegerField(
        "Left file upload(in bites)", default=0, validators=[MinValueValidator(0)]
    )
    theme = models.ForeignKey("themes.Theme", null=True, on_delete=models.SET_NULL)
    agree_data_to_be_sold = models.BooleanField(
        "Agree my data to be sold to vendors", default=False
    )

    def get_theme_url(self):
        if self.theme_id:
            return Theme.objects.cache().get(id=self.theme_id).file.url
        return ""

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})


class UserHistory(models.Model):
    class RecordType(models.TextChoices):
        note = "note", "note"
        create = "create", "create"
        update = "update", "update"
        delete = "delete", "delete"
        warning = "warning", "warning"

    type = models.CharField(choices=RecordType.choices)
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey("User", related_name="history", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey("content_type", "object_id")

    def get_link(self):
        if hasattr(self.object, "get_absolute_url"):
            return self.object.get_absolute_url()
        return ""

    class Meta:
        ordering = ["-created"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return self


class UserAPIToken(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(
        "User", related_name="api_tokens", on_delete=models.CASCADE
    )
    token = models.CharField(max_length=255, unique=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    active_until = models.DateTimeField(null=True)
    permissions = models.JSONField(default=dict)
    last_used = models.DateTimeField(null=True, blank=True)

    permission_template = {
        "music": {
            "listen": "Listen to music",
            "upload": "Upload music",
            "playlist": "Manage playlists",
        },
        "users": {
            "edit": "Edit user profile",
            "delete": "Delete user profile",
        },
        "tools": {
            "shorten": "Shorten links",
        },
        "files": {
            "upload": "Upload files",
            "download": "Download files",
        },
    }

    def __str__(self):
        return self.token

    @property
    def is_active(self) -> bool:
        return self.active_until is None or self.active_until > timezone.now()

    @staticmethod
    def generate_token():
        token = secrets.token_urlsafe(32)
        while UserAPIToken.objects.filter(token=token).exists():
            token = secrets.token_urlsafe(32)
        return token
