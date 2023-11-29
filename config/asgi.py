import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf import settings
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()


from akarpov.common.channels import HeaderAuthMiddleware  # noqa
from config import routing  # noqa

if settings.DEBUG:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": HeaderAuthMiddleware(URLRouter(routing.websocket_urlpatterns)),
    }
)
