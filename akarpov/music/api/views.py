from rest_framework import generics, permissions

from akarpov.common.api.permissions import IsCreatorOrReadOnly
from akarpov.music.api.serializers import (
    FullPlaylistSerializer,
    ListSongSerializer,
    PlaylistSerializer,
    SongSerializer,
)
from akarpov.music.models import Playlist, Song


class ListCreatePlaylistAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PlaylistSerializer

    def get_queryset(self):
        return Playlist.objects.filter(creator=self.request.user)


class RetrieveUpdateDestroyPlaylistAPIView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    permission_classes = [IsCreatorOrReadOnly]
    serializer_class = FullPlaylistSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get_object(self):
        if not self.object:
            self.object = super().get_object()
        return self.object


class ListCreateSongAPIView(generics.ListCreateAPIView):
    serializer_class = ListSongSerializer
    permission_classes = [IsCreatorOrReadOnly]

    def get_queryset(self):
        return Song.objects.all()


class RetrieveUpdateDestroySongAPIView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    permission_classes = [IsCreatorOrReadOnly]
    serializer_class = SongSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get_object(self):
        if not self.object:
            self.object = super().get_object()
        return self.object
