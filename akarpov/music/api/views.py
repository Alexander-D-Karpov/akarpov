from rest_framework import generics, permissions

from akarpov.common.api.pagination import StandardResultsSetPagination
from akarpov.common.api.permissions import IsAdminOrReadOnly, IsCreatorOrReadOnly
from akarpov.music.api.serializers import (
    FullPlaylistSerializer,
    ListSongSerializer,
    PlaylistSerializer,
    SongSerializer,
)
from akarpov.music.models import Playlist, Song, SongUserRating


class LikedSongsContextMixin(generics.GenericAPIView):
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            context["likes_ids"] = (
                SongUserRating.objects.cache()
                .filter(user=self.request.user, like=True)
                .values_list("song_id", flat=True)
            )
        else:
            context["likes_ids"] = []
        return context


class ListCreatePlaylistAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PlaylistSerializer

    def get_queryset(self):
        return Playlist.objects.filter(creator=self.request.user)


class RetrieveUpdateDestroyPlaylistAPIView(
    LikedSongsContextMixin, generics.RetrieveUpdateDestroyAPIView
):
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


class ListCreateSongAPIView(LikedSongsContextMixin, generics.ListCreateAPIView):
    serializer_class = ListSongSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return (
                Song.objects.exclude(
                    id__in=SongUserRating.objects.filter(
                        user=self.request.user
                    ).values_list("song_id", flat=True)
                )
                .prefetch_related("authors")
                .select_related("album")
            )
        return Song.objects.all().prefetch_related("authors").select_related("album")


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


class ListLikedSongsAPIView(generics.ListAPIView):
    serializer_class = ListSongSerializer
    pagination_class = StandardResultsSetPagination
    authentication_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Song.objects.cache()
            .filter(
                id__in=self.request.user.song_likes.objects.cache()
                .all()
                .values_list("song_id", flat=True)
            )
            .prefetch_related("authors")
            .select_related("album")
        )
