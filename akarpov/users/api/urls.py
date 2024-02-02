from django.urls import path

from .views import (
    UserListAPIViewSet,
    UserRetireUpdateSelfAPIViewSet,
    UserRetrieveAPIViewSet,
    UserRetrieveIdAPIAPIView,
    UserUpdatePasswordAPIView,
    VerifyOTPView,
)

app_name = "users_api"


urlpatterns = [
    path("", UserListAPIViewSet.as_view(), name="list"),
    path(
        "self/",
        UserRetireUpdateSelfAPIViewSet.as_view(),
        name="self",
    ),
    path(
        "self/otp/verify/",
        VerifyOTPView.as_view(),
        name="otp_verify",
    ),
    path(
        "self/password",
        UserUpdatePasswordAPIView.as_view(),
        name="password",
    ),
    path(
        "id/<int:pk>",
        UserRetrieveIdAPIAPIView.as_view(),
        name="get_by_id",
    ),
    path(
        "<str:username>",
        UserRetrieveAPIViewSet.as_view(),
        name="get",
    ),
]
