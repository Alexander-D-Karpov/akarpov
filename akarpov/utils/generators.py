import random
import string

from django.contrib.auth.tokens import PasswordResetTokenGenerator

from akarpov.utils.consts import URL_BASE
from akarpov.utils.nums import to_base

URL_CHARACTERS = string.ascii_letters + string.digits + ";,:@&+-_.!~*'()#"


class TokenGenerator(PasswordResetTokenGenerator):
    """token processor for user"""

    def _make_hash_value(self, user, timestamp):
        return str(str(user.pk) + str(timestamp) + str(user.is_active))


def generate_charset(length: int) -> str:
    """Generate a random string of characters of a given length."""
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def get_str_uuid(pk: int) -> str:
    return to_base(pk, list(URL_CHARACTERS))


def get_pk_from_uuid(slug: str) -> int:
    res = 0
    for i, el in enumerate(slug[::-1]):
        if el not in URL_BASE:
            raise ValueError
        res += URL_BASE[el] * 78**i
    return res


def _rand255():
    return random.randint(0, 255)


def generate_hex_color() -> str:
    return f"#{_rand255():02X}{_rand255():02X}{_rand255():02X}"
