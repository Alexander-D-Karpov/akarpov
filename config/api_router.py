from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from akarpov.users.api.views import GenerateUserJWTTokenAPIView, UserRegisterAPIViewSet

app_name = "api"

urlpatterns_v1 = [
    path(
        "auth/",
        include(
            [
                path(
                    "register/",
                    UserRegisterAPIViewSet.as_view(),
                    name="user_register_api",
                ),
                path("token/", obtain_auth_token),
                path("jwt/", GenerateUserJWTTokenAPIView.as_view()),
            ]
        ),
    ),
    path(
        "users/",
        include("akarpov.users.api.urls", namespace="users"),
    ),
    path(
        "gallery/",
        include("akarpov.gallery.api.urls", namespace="gallery"),
    ),
    path(
        "notifications/",
        include("akarpov.notifications.providers.urls", namespace="notifications"),
    ),
    path(
        "blog/",
        include("akarpov.blog.api.urls", namespace="blog"),
    ),
    path(
        "music/",
        include("akarpov.music.api.urls", namespace="music"),
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
