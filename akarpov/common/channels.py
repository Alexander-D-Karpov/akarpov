from importlib import import_module

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer, JsonWebsocketConsumer
from django.conf import settings
from django.contrib.sessions.models import Session

from akarpov.common.jwt import read_jwt
from akarpov.users.models import User

engine = import_module(settings.SESSION_ENGINE)
sessionstore = engine.SessionStore


@database_sync_to_async
def get_user(headers):
    # WARNING headers type is bytes
    if (b"authorization" not in headers or not headers[b"authorization"]) and (
        b"cookie" not in headers or not headers[b"cookie"]
    ):
        return None
    if b"authorization" in headers:
        jwt = headers[b"authorization"].decode()
        data = read_jwt(jwt)
        if not data:
            return None
        payload = data
    elif b"cookie" in headers:
        cookies = dict([x.split("=") for x in headers[b"cookie"].decode().split("; ")])
        if "sessionid" not in cookies:
            return None
        try:
            session = sessionstore(cookies["sessionid"])
            user_id = session["_auth_user_id"]
        except (Session.DoesNotExist, User.DoesNotExist, KeyError):
            return None

        payload = {"id": user_id}
    else:
        payload = {}

    if not payload or "id" not in payload:
        return None

    return payload["id"]


class HeaderAuthMiddleware:
    """Custom middleware to read user auth token from string."""

    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):
        scope["user_id"] = await get_user(dict(scope["headers"]))
        try:
            return await self.app(scope, receive, send)
        except ValueError:
            return


class BaseConsumer(AsyncJsonWebsocketConsumer):
    async def send_error(self, msg):
        await self.send_json({"type": "error", "data": {"msg": msg}})


class SyncBaseConsumer(JsonWebsocketConsumer):
    def send_error(self, msg):
        self.send_json({"type": "error", "data": {"msg": msg}})
