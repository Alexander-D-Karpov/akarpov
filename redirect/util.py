import string

from redirect.settings import settings

URL_CHARACTERS = list(string.ascii_letters + string.digits + ";,:@&-_.!~*'()#")
SLUG_CUTOFF = settings.redirect_slug_cutoff


def slug_to_link_id(slug: str) -> int:
    """Converts given slug to an id of a link."""
    link_id = 0
    try:
        for i, ch in enumerate(slug[:SLUG_CUTOFF - 1:-1]):
            value = URL_CHARACTERS.index(ch)
            link_id += value * len(URL_CHARACTERS) ** i
    except ValueError:
        pass
    return link_id
