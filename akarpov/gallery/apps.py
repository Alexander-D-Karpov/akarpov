from django.apps import AppConfig


class GalleryConfig(AppConfig):
    name = "akarpov.gallery"
    verbose_name = "Gallery"

    def ready(self):
        try:
            import akarpov.gallery.signals  # noqa F401
        except ImportError:
            pass
