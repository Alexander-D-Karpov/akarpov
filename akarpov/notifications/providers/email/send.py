from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from akarpov.notifications.models import Notification
from akarpov.users.models import User


def send_notification(notification: Notification) -> bool:
    if not notification.meta or all(
        ["email" not in notification.meta, "user_id" not in notification.meta]
    ):
        raise KeyError(
            f"can't send notification {notification.id}, email/user_id is not found"
        )
    if "email" in notification.meta:
        email = notification.meta["email"]
        username = ""
    else:
        user = User.objects.get(id=notification.meta["user_id"])
        email = user.email
        username = user.username
    message = render_to_string(
        "email/notification.html", {"username": username, "body": notification.body}
    )
    send_mail(
        notification.title,
        notification.body,
        settings.EMAIL_FROM,
        [email],
        fail_silently=False,
        html_message=message,
    )
    return True
