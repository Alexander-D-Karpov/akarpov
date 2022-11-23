from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from akarpov.users.api.views import (
    UserListViewSet,
    UserRegisterViewSet,
    UserRetireUpdateSelfViewSet,
    UserRetrieveIdViewSet,
    UserRetrieveViewSet,
)

urlpatterns_v1 = [
    path(
        "auth/",
        include(
            [
                path(
                    "register/", UserRegisterViewSet.as_view(), name="user_register_api"
                ),
                path("token/", obtain_auth_token),
            ]
        ),
    ),
    path(
        "users/",
        include(
            [
                path("", UserListViewSet.as_view(), name="user_list_api"),
                path(
                    "self/",
                    UserRetireUpdateSelfViewSet.as_view(),
                    name="user_get_update_delete_self_api",
                ),
                path(
                    "id/<int:pk>",
                    UserRetrieveIdViewSet.as_view(),
                    name="user_retrieve_id_api",
                ),
                path(
                    "<str:username>",
                    UserRetrieveViewSet.as_view(),
                    name="user_retrieve_username_api",
                ),
            ]
        ),
    ),
]

urlpatterns = [path("v1/", include(urlpatterns_v1))]
