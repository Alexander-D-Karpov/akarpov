from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "akarpov.notifications"
    verbose_name = "Notifications"

    def ready(self):
        try:
            import akarpov.notifications.signals  # noqa F401
        except ImportError:
            pass
