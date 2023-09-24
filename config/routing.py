from django.urls import re_path

from akarpov.music.consumers import RadioConsumer
from akarpov.notifications.providers.site.consumers import NotificationsConsumer

websocket_urlpatterns = [
    re_path(r"ws/radio/", RadioConsumer.as_asgi()),
    re_path(r"ws/notifications/", NotificationsConsumer.as_asgi()),
]
