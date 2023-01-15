from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from akarpov.users.api.views import UserRegisterViewSet

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
        include("akarpov.users.api.urls"),
    ),
    path("file/", include("akarpov.files.api.urls")),
    path(
        "tools/",
        include([path("qr/", include("akarpov.tools.qr.api.urls"))]),
    ),
]

urlpatterns = [path("v1/", include(urlpatterns_v1))]
