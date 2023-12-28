from django.urls import include, path

from akarpov.users.views import (
    enable_2fa_view,
    enforce_otp_login,
    user_detail_view,
    user_history_delete_view,
    user_history_view,
    user_redirect_view,
    user_update_view,
)

app_name = "users"
urlpatterns = [
    path("redirect/", view=user_redirect_view, name="redirect"),
    path("themes/", include("akarpov.users.themes.urls", namespace="themes")),
    path("update/", view=user_update_view, name="update"),
    path("history/", view=user_history_view, name="history"),
    path("history/delete", view=user_history_delete_view, name="history_delete"),
    path("<str:username>/", view=user_detail_view, name="detail"),
    path("2fa/login", enforce_otp_login, name="enforce_otp_login"),
    path("2fa/enable", enable_2fa_view, name="enable_2fa"),
]
