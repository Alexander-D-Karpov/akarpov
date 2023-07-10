from django.urls import re_path

from akarpov.music.consumers import RadioConsumer

websocket_urlpatterns = [
    re_path(r"ws/radio/", RadioConsumer.as_asgi()),
]
