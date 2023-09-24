from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from akarpov.notifications.models import Notification
from akarpov.notifications.providers.site.api.serializers import (
    SiteNotificationSerializer,
)


def send_notification(notification: Notification) -> bool:
    if (
        not notification.meta
        or "user_id" not in notification.meta
        or not notification.meta["user_id"]
    ):
        raise KeyError(
            f"can't send notification {notification.id}, user_id is not found"
        )
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notifications_{notification.meta['user_id']}",
        {
            "type": "notification",
            "data": SiteNotificationSerializer().to_representation(notification),
        },
    )
    if "conformation" in notification.meta and notification.meta["conformation"]:
        # no view conformation required, only pop up on site
        return False
    return True
