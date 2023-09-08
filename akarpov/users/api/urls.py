from django.urls import path

from .views import (
    UserListViewSet,
    UserRetireUpdateSelfViewSet,
    UserRetrieveIdViewSet,
    UserRetrieveViewSet,
)

app_name = "users_api"


urlpatterns = [
    path("", UserListViewSet.as_view(), name="list"),
    path(
        "self/",
        UserRetireUpdateSelfViewSet.as_view(),
        name="self",
    ),
    path(
        "id/<int:pk>",
        UserRetrieveIdViewSet.as_view(),
        name="get_by_id",
    ),
    path(
        "<str:username>",
        UserRetrieveViewSet.as_view(),
        name="get",
    ),
]
