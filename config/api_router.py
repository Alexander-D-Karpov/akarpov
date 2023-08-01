from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from akarpov.users.api.views import UserRegisterViewSet

app_name = "api"

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
        include("akarpov.users.api.urls", namespace="users"),
    ),
    path(
        "blog/",
        include("akarpov.blog.api.urls", namespace="blog"),
    ),
    path(
        "tools/",
        include(
            "akarpov.tools.api.urls",
            namespace="tools",
        ),
    ),
]

urlpatterns = [path("v1/", include(urlpatterns_v1))]
