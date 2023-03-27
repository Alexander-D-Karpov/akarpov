from channels.db import database_sync_to_async

from akarpov.common.jwt import read_jwt


@database_sync_to_async
def get_user(headers):
    # WARNING headers type is bytes
    if b"authorization" not in headers or not headers[b"authorization"]:
        return False

    jwt = headers[b"authorization"].decode()
    payload = read_jwt(jwt)

    if not payload or "id" not in payload:
        return False

    return payload["id"]


class HeaderAuthMiddleware:
    """Custom middleware to read user auth token from string."""

    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):
        scope["user"] = await get_user(dict(scope["headers"]))

        return await self.app(scope, receive, send)