from django.urls import include, path

from akarpov.blog.api.views import (
    CreateDeleteCommentRateApiView,
    CreateDeletePostRating,
    CreatePostApiView,
    GetUpdateDeletePostApiView,
    ListCreateCommentApiView,
    ListPostsApiView,
    RetrieveUpdateDeleteCommentApiView,
)
from akarpov.users.api.views import (
    TokenObtainPairView,
    TokenRefreshView,
    UserEmailValidationViewSet,
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
                path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
                path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
                path(
                    "register/", UserRegisterViewSet.as_view(), name="user_register_api"
                ),
                path(
                    "prove_email/",
                    UserEmailValidationViewSet.as_view(),
                    name="user_email_validation_api",
                ),
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
    # blog
    path(
        "blog/",
        include(
            [
                path("", ListPostsApiView.as_view(), name="list_all_posts_api"),
                path("create/", CreatePostApiView.as_view(), name="create_post_api"),
                path(
                    "<str:slug>",
                    GetUpdateDeletePostApiView.as_view(),
                    name="retrieve_update_delete_post_api",
                ),
                path(
                    "<str:slug>/rating/",
                    CreateDeletePostRating.as_view(),
                    name="create_delete_post_rating_api",
                ),
                path(
                    "<str:slug>/comments/",
                    ListCreateCommentApiView.as_view(),
                    name="list_create_comment_api",
                ),
                path(
                    "comments/<int:pk>",
                    RetrieveUpdateDeleteCommentApiView.as_view(),
                    name="list_create_comment_api",
                ),
                path(
                    "comments/<int:pk>/vote_up/",
                    CreateDeleteCommentRateApiView.as_view(),
                    name="list_create_comment_api",
                ),
            ]
        ),
    ),
]

urlpatterns = [path("v1/", include(urlpatterns_v1))]
