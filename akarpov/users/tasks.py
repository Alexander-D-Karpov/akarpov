from celery import shared_task
from django.utils import timezone

from akarpov.users.models import UserAPIToken


@shared_task
def set_last_active_token(token: str):
    token = UserAPIToken.objects.get(token=token)
    token.last_used = timezone.now()
    token.save()
