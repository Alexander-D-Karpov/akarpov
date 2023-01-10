from django.urls import path
from .views import (
    UserListViewSet,
    UserRetireUpdateSelfViewSet,
    UserRetrieveIdViewSet,
    UserRetrieveViewSet,
)

urlpatterns = [
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
