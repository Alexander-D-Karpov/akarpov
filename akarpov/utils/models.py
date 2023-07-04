from functools import lru_cache

from django.apps import apps
from django.db.models import Model

from akarpov.users.models import User


def get_object_name(obj: Model) -> str:
    if hasattr(obj, "title"):
        return obj.title
    elif hasattr(obj, "name"):
        return obj.name
    elif hasattr(obj, "__str__"):
        return obj.__str__()
    return ""


def get_object_user(obj: Model) -> User | None:
    if hasattr(obj, "creator"):
        return obj.creator
    elif hasattr(obj, "user"):
        return obj.user
    elif hasattr(obj, "owner"):
        return obj.owner
    return None


@lru_cache
def get_app_verbose_name(app: str) -> str:
    return apps.get_app_config(app).verbose_name
