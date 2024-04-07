from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object
from rest_framework.authentication import BaseAuthentication

from akarpov.users.models import User, UserAPIToken
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

        return User.objects.cache().get(id=token.user_id), token


class UserTokenAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "akarpov.users.api.authentification.UserTokenAuthentication"
    name = "UserTokenAuthentication"

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name="Authorization", token_prefix="Bearer"
        )
