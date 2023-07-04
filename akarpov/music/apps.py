from django.apps import AppConfig


class MusicConfig(AppConfig):
    verbose_name = "Music"
    name = "akarpov.music"

    def ready(self):
        try:
            import akarpov.music.signals  # noqa F401
        except ImportError:
            pass
