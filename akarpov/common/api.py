from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import SAFE_METHODS, BasePermission

from akarpov.utils.models import get_object_user


class SmallResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class BigResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class IsCreatorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS
            or request.user
            and get_object_user(view.get_object()) == request.user
        )


class SetUserModelSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        creator = self.context["request"].user
        obj = self.Meta.model.objects.create(creator=creator, **validated_data)
        return obj
