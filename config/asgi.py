import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from akarpov.common.channels import HeaderAuthMiddleware
from config import routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": HeaderAuthMiddleware(URLRouter(routing.websocket_urlpatterns)),
    }
)
