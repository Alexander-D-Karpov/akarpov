from rest_framework import generics, permissions

from akarpov.common.api.pagination import StandardResultsSetPagination
from akarpov.common.api.permissions import IsAdminOrReadOnly, IsCreatorOrReadOnly
from akarpov.music.api.serializers import (
    AddSongToPlaylistSerializer,
    AlbumSerializer,
    AuthorSerializer,
    FullAlbumSerializer,
    FullAuthorSerializer,
    FullPlaylistSerializer,
    LikeDislikeSongSerializer,
    ListPlaylistSerializer,
    ListSongSerializer,
    PlaylistSerializer,
    SongSerializer,
)
from akarpov.music.models import Album, Author, Playlist, Song, SongUserRating


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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = PlaylistSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Playlist.objects.filter(creator=self.request.user).select_related(
                "creator"
            )
        return Playlist.objects.filter(private=False).select_related("creator")


class ListPublicPlaylistAPIView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PlaylistSerializer

    def get_queryset(self):
        return Playlist.objects.filter(private=False)


class RetrieveUpdateDestroyPlaylistAPIView(
    LikedSongsContextMixin, generics.RetrieveUpdateDestroyAPIView
):
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    permission_classes = [IsCreatorOrReadOnly]
    serializer_class = FullPlaylistSerializer

    def get_queryset(self):
        qs = Playlist.objects.filter(private=False)
        if self.request.user.is_authenticated:
            qs = Playlist.objects.filter(creator=self.request.user) | qs
        return qs.select_related("creator")


class ListCreateSongAPIView(LikedSongsContextMixin, generics.ListCreateAPIView):
    serializer_class = ListSongSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return (
                Song.objects.all()
                .exclude(
                    id__in=SongUserRating.objects.filter(
                        user=self.request.user,
                        like=False,
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

    def get_queryset(self):
        return Song.objects.all()


class ListSongPlaylistsAPIView(generics.ListAPIView):
    serializer_class = ListPlaylistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Playlist.objects.filter(
            songs__song__slug=self.kwargs["slug"], creator=self.request.user
        )


class ListLikedSongsAPIView(generics.ListAPIView):
    serializer_class = ListSongSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["likes"] = True
        return context

    def get_queryset(self):
        return (
            Song.objects.cache()
            .filter(
                id__in=SongUserRating.objects.cache()
                .filter(user=self.request.user, like=True)
                .values_list("song_id", flat=True)
            )
            .prefetch_related("authors")
            .select_related("album")
        )


class ListDislikedSongsAPIView(generics.ListAPIView):
    serializer_class = ListSongSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["likes"] = False
        return context

    def get_queryset(self):
        return (
            Song.objects.cache()
            .filter(
                id__in=SongUserRating.objects.cache()
                .filter(user=self.request.user, like=True)
                .values_list("song_id", flat=False)
            )
            .prefetch_related("authors")
            .select_related("album")
        )


class AddSongToPlaylistAPIView(generics.CreateAPIView):
    serializer_class = AddSongToPlaylistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Playlist.objects.filter(creator=self.request.user)

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context()
        context["create"] = True
        return context


class RemoveSongFromPlaylistAPIView(generics.DestroyAPIView):
    serializer_class = AddSongToPlaylistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Playlist.objects.filter(creator=self.request.user)

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context()
        context["create"] = False
        return context


class LikeSongAPIView(generics.CreateAPIView):
    serializer_class = LikeDislikeSongSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SongUserRating.objects.all()

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context()
        context["like"] = True
        return context


class DislikeSongAPIView(generics.CreateAPIView):
    serializer_class = LikeDislikeSongSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SongUserRating.objects.all()

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context()
        context["like"] = False
        return context


class ListAlbumsAPIView(generics.ListAPIView):
    serializer_class = AlbumSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Album.objects.all()


class RetrieveUpdateDestroyAlbumAPIView(
    LikedSongsContextMixin, generics.RetrieveUpdateDestroyAPIView
):
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = FullAlbumSerializer


class ListAuthorsAPIView(generics.ListAPIView):
    serializer_class = AuthorSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Author.objects.all()


class RetrieveUpdateDestroyAuthorAPIView(
    LikedSongsContextMixin, generics.RetrieveUpdateDestroyAPIView
):
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = FullAuthorSerializer
