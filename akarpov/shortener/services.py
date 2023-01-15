from django.conf import settings

from akarpov.shortener.models import Link
from akarpov.utils.generators import generate_charset, get_pk_from_uuid, get_str_uuid

lenght = settings.SHORTENER_SLUG_LENGTH


def generate_slug(pk: int) -> str:
    if settings.SHORTENER_ADD_SLUG:
        slug = generate_charset(lenght)
        return slug + get_str_uuid(pk)
    return get_str_uuid(pk)


def get_link_from_slug(slug: str, check_whole=False) -> Link | bool:
    if settings.SHORTENER_ADD_SLUG and not check_whole:
        payload = slug[lenght:]
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
