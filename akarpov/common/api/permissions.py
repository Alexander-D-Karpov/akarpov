from rest_framework.permissions import SAFE_METHODS, BasePermission

from akarpov.utils.models import get_object_user


class IsCreatorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS
            or request.user
            and get_object_user(view.get_object()) == request.user
        )


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS or request.user and request.user.is_staff
        )
