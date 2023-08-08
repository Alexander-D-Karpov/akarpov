from sqlalchemy.orm import Session

from redirect.db import models
from redirect.util import slug_to_link_id


class LinkNotFoundException(Exception):
    def __init__(self, slug: str):
        self.slug = slug


def get_link(db: Session, link_id: int):
    """Gets short link metdata by its id.

    :param db Open connection to a database
    :param link_id id of the link

    :return link metadata"""
    return db.query(models.Link).filter(models.Link.id == link_id).first()


_get_link_by_slug_cache = {}


def get_link_by_slug(db: Session, slug: str) -> tuple[int, str]:
    """Converts slug to id and gets related link target.

    :param db Open connection to a database
    :param slug of the link

    :raise LinkNotFoundException if link is not found
    :return target link id & url"""
    if slug in _get_link_by_slug_cache:
        return _get_link_by_slug_cache[slug]

    link = get_link(db, slug_to_link_id(slug))
    if link is None or not link.enabled:
        raise LinkNotFoundException(slug)

    _get_link_by_slug_cache[slug] = (link.id, link.source)
    return link.id, link.source
