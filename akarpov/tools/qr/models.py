import uuid

from django.db import models


class QR(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    body = models.TextField()
    image = models.ImageField()
    user = models.ForeignKey(
        "users.User", related_name="generated_qrs", blank=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return f"qr {self.body}"
