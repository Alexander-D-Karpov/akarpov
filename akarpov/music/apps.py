from django.apps import AppConfig


class MusicConfig(AppConfig):
    verbose_name = "Music"
    name = "akarpov.music"

    def ready(self):
        import akarpov.music.signals  # noqa F401
