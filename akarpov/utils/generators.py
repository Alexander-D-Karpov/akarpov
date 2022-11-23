import random
import string

from django.contrib.auth.tokens import PasswordResetTokenGenerator


class TokenGenerator(PasswordResetTokenGenerator):
    """token processor for user"""

    def _make_hash_value(self, user, timestamp):
        return str(str(user.pk) + str(timestamp) + str(user.is_active))


def generate_charset(length: int) -> str:
    """Generate a random string of characters of a given length."""
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def _rand255():
    return random.randint(0, 255)


def generate_hex_color() -> str:
    return f"#{_rand255():02X}{_rand255():02X}{_rand255():02X}"
