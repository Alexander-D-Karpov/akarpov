import functools

from channels.generic.websocket import AsyncJsonWebsocketConsumer, JsonWebsocketConsumer


def login_required(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.scope.get("user", False) or not self.scope["user"].is_authenticated:
            self.send_error("Требуется авторизация")
        else:
            return func(self, *args, **kwargs)

    return wrapper


class BaseConsumer(AsyncJsonWebsocketConsumer):
    async def send_error(self, msg):
        await self.send_json({"type": "error", "data": {"msg": msg}})


class SyncBaseConsumer(JsonWebsocketConsumer):
    def send_error(self, msg):
        self.send_json({"type": "error", "data": {"msg": msg}})
