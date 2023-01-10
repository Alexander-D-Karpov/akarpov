from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny

from akarpov.tools.qr.models import QR
from .serializers import QRSerializer


class QRViewSet(generics.ListCreateAPIView, generics.RetrieveAPIView, GenericViewSet):
    serializer_class = QRSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        print(self.kwargs)
        return get_object_or_404(QR, pk=self.kwargs["pk"])

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return QR.objects.filter(user=self.request.user)
        return QR.objects.none()
