from cacheops import cached_as
from django.shortcuts import redirect
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.exceptions import AuthenticationFailed


class EmailVerificationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            if not request.user.is_verified:
                raise AuthenticationFailed("Email is not verified")
        return None


class Enforce2FAMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check user is authenticated and OTP token input is not completed
        is_authenticated = request.user.is_authenticated
        otp_not_verified = not request.session.get("otp_verified", False)
        on_2fa_page = resolve(request.path_info).url_name == "enforce_otp_login"

        # Caches the checker for has_otp_device
        @cached_as(
            TOTPDevice, timeout=15 * 60
        )  # consider appropriate time for your use case
        def has_otp_device(user):
            return TOTPDevice.objects.devices_for_user(user, confirmed=True).exists()

        # Enforce OTP token input, if user is authenticated, has OTP enabled but has not verified OTP
        if (
            is_authenticated
            and has_otp_device(request.user)
            and otp_not_verified
            and not on_2fa_page
        ):
            request.session["next"] = request.get_full_path()
            return redirect("users:enforce_otp_login")

        return response
