from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FilesConfig(AppConfig):
    name = "akarpov.files"
    verbose_name = _("Files")

    def ready(self):
        try:
            import akarpov.files.signals  # noqa F401
        except ImportError:
            pass
