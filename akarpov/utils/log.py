import logging

from django.conf import settings


class RequireDbDebugTrue(logging.Filter):
    def filter(self, record) -> bool:
        return settings.DB_DEBUG
