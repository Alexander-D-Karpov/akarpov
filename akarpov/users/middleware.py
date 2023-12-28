from django.shortcuts import redirect
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
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

        # Enforce OTP token input, if user is authenticated but has not verified OTP, and is NOT on the 2FA page
        if is_authenticated and otp_not_verified and not on_2fa_page:
            request.session["next"] = request.get_full_path()
            return redirect("users:enforce_otp_login")

        return response
