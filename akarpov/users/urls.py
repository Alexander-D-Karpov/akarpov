from django.urls import include, path

from akarpov.users.views import (
    create_token,
    delete_token,
    enable_2fa_view,
    enforce_otp_login,
    list_tokens,
    user_detail_view,
    user_history_delete_view,
    user_history_view,
    user_redirect_view,
    user_update_view,
    view_token,
)

app_name = "users"
urlpatterns = [
    path("redirect/", view=user_redirect_view, name="redirect"),
    path("themes/", include("akarpov.users.themes.urls", namespace="themes")),
    path("update/", view=user_update_view, name="update"),
    path("history/", view=user_history_view, name="history"),
    path("history/delete", view=user_history_delete_view, name="history_delete"),
    path("<str:username>", view=user_detail_view, name="detail"),
    path("2fa/login", enforce_otp_login, name="enforce_otp_login"),
    path("2fa/enable", enable_2fa_view, name="enable_2fa"),
    path("tokens/", list_tokens, name="list_tokens"),
    path("tokens/create/", create_token, name="create_token"),
    path("tokens/<int:token_id>/", view_token, name="view_token"),
    path("tokens/<int:token_id>/delete/", delete_token, name="delete_token"),
]
