from rest_framework.authentication import BaseAuthentication

from akarpov.users.models import UserAPIToken
from akarpov.users.tasks import set_last_active_token


class UserTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if "Authorization" not in request.headers:
            return None
        token = request.headers["Authorization"]
        if " " in token:
            token = token.split(" ")[1]
        try:
            token = UserAPIToken.objects.cache().get(token=token)
        except UserAPIToken.DoesNotExist:
            return None
        if not token.is_active:
            return None
        set_last_active_token.delay(token.token)

        return token.user, token
