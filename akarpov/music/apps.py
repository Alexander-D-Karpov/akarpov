from django.apps import AppConfig
from django.core.exceptions import AppRegistryNotReady


class MusicConfig(AppConfig):
    verbose_name = "Music"
    name = "akarpov.music"

    def ready(self):
        try:
            import akarpov.music.signals  # noqa F401
        except ImportError:
            pass
        try:
            from akarpov.music.tasks import start_next_song

            start_next_song.apply_async(
                kwargs={"previous_ids": []},
                countdown=5,
            )
        except AppRegistryNotReady:
            pass
