from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BlogConfig(AppConfig):
    verbose_name = _("Blog")
    name = "akarpov.blog"

    def ready(self):
        try:
            import akarpov.blog.signals  # noqa F401
        except ImportError:
            pass
