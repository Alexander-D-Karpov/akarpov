from importlib import import_module

from celery import shared_task

from akarpov.notifications.models import Notification

providers = {x[1]: x[0] for x in Notification.NotificationProviders.choices}


@shared_task
def run_send_notification(pk):
    instance = Notification.objects.get(pk=pk)
    provider = import_module(instance.provider)
    instance.delivered = provider.send_notification(instance)
    instance.save()


@shared_task
def run_create_send_notification(title: str, body: str, provider: str, **kwargs):
    if provider != "*" and provider not in providers:
        raise ValueError(f"no such provider: {provider}")
    if provider == "*":
        for provider in providers:
            Notification.objects.create(
                title=title, body=body, provider=providers[provider], meta=kwargs
            )
    else:
        Notification.objects.create(
            title=title, body=body, provider=providers[provider], meta=kwargs
        )

    return
