from django.urls import path

from akarpov.users.views import (
    user_detail_view,
    user_history_delete_view,
    user_history_view,
    user_redirect_view,
    user_update_view,
)

app_name = "users"
urlpatterns = [
    path("redirect/", view=user_redirect_view, name="redirect"),
    path("update/", view=user_update_view, name="update"),
    path("history/", view=user_history_view, name="history"),
    path("history/delete", view=user_history_delete_view, name="history_delete"),
    path("<str:username>/", view=user_detail_view, name="detail"),
]
