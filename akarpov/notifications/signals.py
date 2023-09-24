from django.db.models.signals import post_save
from django.dispatch import receiver

from akarpov.notifications.models import Notification
from akarpov.notifications.tasks import run_send_notification


@receiver(post_save, sender=Notification)
def notification_create(sender, instance: Notification, created, **kwargs):
    if created:
        run_send_notification.apply_async(kwargs={"pk": instance.pk}, countdown=2)
