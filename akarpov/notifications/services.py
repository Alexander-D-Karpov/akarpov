from akarpov.notifications.tasks import run_create_send_notification


def send_notification(title: str, body: str, provider: str, **kwargs):
    run_create_send_notification.apply_async(
        kwargs={"title": title, "body": body, "provider": provider} | kwargs
    )
