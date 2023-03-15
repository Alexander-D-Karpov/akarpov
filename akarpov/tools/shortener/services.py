from django.conf import settings

from akarpov.tools.shortener.signals import Link
from akarpov.utils.generators import get_pk_from_uuid

length = settings.SHORTENER_SLUG_LENGTH


def get_link_from_slug(slug: str, check_whole=False) -> Link | bool:
    if settings.SHORTENER_ADD_SLUG and not check_whole:
        payload = slug[length:]
        pk = get_pk_from_uuid(payload)
        try:
            return Link.objects.get(pk=pk)
        except Link.DoesNotExist:
            return get_link_from_slug(slug, check_whole=True)
    pk = get_pk_from_uuid(slug)
    try:
        return Link.objects.get(pk=pk)
    except Link.DoesNotExist:
        return False
