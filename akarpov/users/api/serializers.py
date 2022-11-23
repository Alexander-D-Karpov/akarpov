from rest_framework import serializers

from akarpov.users.models import User
from akarpov.users.services.email_validation import activate


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
            "id": {"read_only": True},
        }


class UserEmailVerification(serializers.Serializer):
    token = serializers.CharField(max_length=255)

    def validate_token(self, token):
        activate(token.split(":")[0], token.split(":")[1])
        return token


class UserPublicInfoSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="user_retrieve_username_api", lookup_field="username"
    )

    class Meta:
        model = User
        fields = ("id", "username", "url", "image_cropped")


class UserFullPublicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_superuser", "about", "image")


class UserFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "is_staff",
            "is_superuser",
            "about",
            "image",
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "email": {"read_only": True},
            "is_staff": {"read_only": True},
            "is_superuser": {"read_only": True},
        }
