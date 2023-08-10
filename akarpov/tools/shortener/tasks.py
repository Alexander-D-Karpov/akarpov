from importlib import import_module

from celery import shared_task
from django.conf import settings
from django.contrib.sessions.models import Session

from akarpov.tools.shortener.models import Link, LinkViewMeta
from akarpov.users.models import User

engine = import_module(settings.SESSION_ENGINE)
sessionstore = engine.SessionStore


@shared_task
def save_view_meta(pk, ip, user_agent, user_id):
    link = Link.objects.get(pk=pk)
    meta = LinkViewMeta(link=link, ip=ip, user_agent=user_agent)
    if user_id:
        if type(user_id) is int:
            meta.user_id = user_id
        elif type(user_id) is str:
            try:
                session = sessionstore(user_id)
                meta.user_id = session["_auth_user_id"]
            except (Session.DoesNotExist, User.DoesNotExist, KeyError):
                pass
    meta.save()
    link.viewed += 1
    link.save(update_fields=["viewed"])
    return
