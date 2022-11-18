from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import AuthenticationFailed


class EmailVerificationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            if not request.user.is_verified:
                raise AuthenticationFailed("Email is not verified")
        return None
