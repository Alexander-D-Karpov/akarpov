from functools import lru_cache
from secrets import compare_digest

from django.conf import settings

from akarpov.tools.shortener.signals import Link
from akarpov.utils.generators import get_pk_from_uuid

if hasattr(settings, "SHORTENER_SLUG_LENGTH"):
    length = settings.SHORTENER_SLUG_LENGTH
else:
    length = 0


def get_link_from_slug(slug: str, check_whole=True) -> Link | bool:
    if settings.SHORTENER_ADD_SLUG and check_whole:
        payload = slug[length:]
        pk = get_pk_from_uuid(payload)
        try:
            link = Link.objects.get(pk=pk)
            if not compare_digest(link.slug, slug):
                return False
            return link
        except Link.DoesNotExist:
            return get_link_from_slug(slug, check_whole=False)
    pk = get_pk_from_uuid(slug)
    try:
        link = Link.objects.get(pk=pk)
        return link
    except Link.DoesNotExist:
        return False


@lru_cache
def get_cached_link_source(slug: str) -> tuple[bool, bool] | tuple[str, int]:
    # TODO: add TTL here or update cache on link update
    link = get_link_from_slug(slug)
    if link:
        return link.source, link.pk
    return False, False
