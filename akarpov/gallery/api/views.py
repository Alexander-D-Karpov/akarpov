from rest_framework import generics, parsers
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from akarpov.common.api.pagination import StandardResultsSetPagination
from akarpov.gallery.api.serializers import ImageSerializer
from akarpov.gallery.models import Image


class ListCreateImageAPIView(generics.ListCreateAPIView):
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.request.user.images.all()
        return Image.objects.filter(public=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
