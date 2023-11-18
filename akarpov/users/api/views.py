from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from akarpov.common.api.pagination import SmallResultsSetPagination
from akarpov.common.jwt import sign_jwt
from akarpov.users.api.serializers import (
    UserEmailVerification,
    UserFullPublicInfoSerializer,
    UserFullSerializer,
    UserPublicInfoSerializer,
    UserRegisterSerializer,
    UserUpdatePassword,
)
from akarpov.users.models import User


class UserRegisterAPIViewSet(generics.CreateAPIView):
    """Creates new user and sends verification email"""

    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        operation_id="auth_user_register",
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class GenerateUserJWTTokenAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: OpenApiTypes.STR})
    def get(self, request, *args, **kwargs):
        return Response(data=sign_jwt(data={"id": self.request.user.id}))


class UserEmailValidationAPIViewSet(views.APIView):
    """Receives token from email and activates user"""

    permission_classes = [permissions.AllowAny]
    serializer_class = UserEmailVerification

    @extend_schema(
        operation_id="auth_user_email_prove",
        request=UserEmailVerification(),
        responses={200: "", 400: {"message": "Incorrect token"}},
    )
    def post(self, request):
        serializer = UserEmailVerification(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_200_OK)


class UserListAPIViewSet(generics.ListAPIView):
    serializer_class = UserPublicInfoSerializer
    pagination_class = SmallResultsSetPagination

    permission_classes = [permissions.AllowAny]
    queryset = User.objects.get_queryset().filter(is_active=True).order_by("id")

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class UserRetrieveAPIViewSet(generics.RetrieveAPIView):
    """Returns user's instance on username"""

    serializer_class = UserFullPublicInfoSerializer
    lookup_field = "username"

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        operation_id="user_username_lookup",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserRetrieveIdAPIAPIView(UserRetrieveAPIViewSet):
    """Returns user's instance on user's id"""

    lookup_field = "pk"

    @extend_schema(
        operation_id="user_id_lookup",
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class UserRetireUpdateSelfAPIViewSet(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserFullSerializer

    def get_object(self):
        return self.request.user


class UserUpdatePasswordAPIView(generics.UpdateAPIView):
    serializer_class = UserUpdatePassword

    def get_object(self):
        return self.request.user
