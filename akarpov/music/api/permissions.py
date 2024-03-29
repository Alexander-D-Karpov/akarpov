from rest_framework import permissions

from akarpov.users.models import User, UserAPIToken


class GetBaseMusicPermission(permissions.BasePermission):
    def get_token_data(self, request) -> (dict, User | None):
        try:
            token = request.headers["Authorization"]
            if " " in token:
                token = token.split(" ")[1]
        except (KeyError, IndexError):
            return {
                "listen": False,
                "upload": False,
                "playlist": False,
            }, None
        try:
            token = UserAPIToken.objects.cache().get(token=token)
        except UserAPIToken.DoesNotExist:
            return {
                "listen": False,
                "upload": False,
                "playlist": False,
            }, None
        if "music" not in token.permissions:
            return {
                "listen": False,
                "upload": False,
                "playlist": False,
            }, token.user
        return token.permissions["music"], token.user


class CanListenToMusic(GetBaseMusicPermission):
    def has_permission(self, request, view):
        token_data = self.get_token_data(request)
        if "listen" in token_data:
            return token_data["listen"]
        return False


class CanUploadMusic(GetBaseMusicPermission):
    def has_permission(self, request, view):
        token_data = self.get_token_data(request)
        if "upload" in token_data:
            return token_data["upload"]
        return False


class CanManagePlaylists(GetBaseMusicPermission):
    def has_permission(self, request, view):
        token_data = self.get_token_data(request)
        if "playlist" in token_data:
            return token_data["playlist"]
        return False
