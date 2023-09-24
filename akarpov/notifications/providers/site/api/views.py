from rest_framework import generics, permissions

from akarpov.common.api import StandardResultsSetPagination
from akarpov.notifications.models import Notification
from akarpov.notifications.providers.site.api.serializers import (
    SiteNotificationSerializer,
)


class ListNotificationsAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SiteNotificationSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Notification.objects.filter(meta__user_id=self.request.user.id)


# TODO: add read notification url here
