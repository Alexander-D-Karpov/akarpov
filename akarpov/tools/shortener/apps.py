from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ShortenerConfig(AppConfig):
    name = "akarpov.tools.shortener"
    verbose_name = _("Link shortener")

    def ready(self):
        try:
            import akarpov.shortener.signals  # noqa F401
        except ImportError:
            pass
