from django.db import models
from django_extensions.db.models import TimeStampedModel


class Notification(TimeStampedModel):
    class NotificationProviders(models.TextChoices):
        site = "akarpov.notifications.providers.site", "site"
        email = "akarpov.notifications.providers.email", "email"

    title = models.CharField(max_length=255)
    body = models.TextField(max_length=5000, null=True, blank=True)
    provider = models.CharField(choices=NotificationProviders.choices)
    meta = models.JSONField(null=True)
    delivered = models.BooleanField(default=False)

    def __str__(self):
        return self.title
