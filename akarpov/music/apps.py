from django.apps import AppConfig


class MusicConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "akarpov.music"

    def ready(self):
        try:
            import akarpov.music.signals  # noqa F401
        except ImportError:
            pass
