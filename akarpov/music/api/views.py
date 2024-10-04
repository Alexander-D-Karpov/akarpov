from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics, permissions
from rest_framework.response import Response

from akarpov.common.api.pagination import StandardResultsSetPagination
from akarpov.common.api.permissions import IsAdminOrReadOnly, IsCreatorOrReadOnly
from akarpov.music.api.serializers import (
    AddSongToPlaylistSerializer,
    AnonMusicUserSerializer,
    FullAlbumSerializer,
    FullAuthorSerializer,
    FullPlaylistSerializer,
    LikeDislikeSongSerializer,
    ListAlbumSerializer,
    ListAuthorSerializer,
    ListenSongSerializer,
    ListPlaylistSerializer,
    ListSongSerializer,
    ListSongSlugsSerializer,
    PlaylistSerializer,
    SongSerializer,
    AllSearchSerializer,
)
from akarpov.music.models import (
    Album,
    Author,
    Playlist,
    Song,
    SongUserRating,
    UserListenHistory,
)
from akarpov.music.services.search import search_song, search_album, search_author
from akarpov.music.tasks import listen_to_song
from akarpov.users.models import User


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


class ListBaseSongAPIView(generics.ListAPIView):
    def get_queryset(self):
        search = self.request.query_params.get("search", None)
        if search:
            qs = search_song(search)
        else:
            qs = Song.objects.cache()

        if "sort" in self.request.query_params:
            sorts = self.request.query_params["sort"].split(",")
            for sort in sorts:
                pref = "-"
                if sort.startswith("-"):
                    pref = ""
                if sort == "likes":
                    qs = qs.order_by(pref + "likes")
                elif sort == "length":
                    qs = qs.order_by(pref + "length")
                elif sort == "played":
                    qs = qs.order_by(pref + "played")
                elif sort == "uploaded":
                    qs = qs.order_by(pref + "created")

        if self.request.user.is_authenticated:
            return qs.exclude(
                id__in=SongUserRating.objects.filter(
                    user=self.request.user,
                    like=False,
                ).values_list("song_id", flat=True)
            )
        return qs


class ListCreateSongAPIView(
    LikedSongsContextMixin, generics.ListCreateAPIView, ListBaseSongAPIView
):
    serializer_class = ListSongSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search query",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="sort",
                description="Sorting algorithm",
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        "Default",
                        description="by date added",
                        value=None,
                    ),
                    OpenApiExample(
                        "played",
                        description="by total times played",
                        value="played",
                    ),
                    OpenApiExample(
                        "likes",
                        description="by total likes",
                        value="likes",
                    ),
                    OpenApiExample(
                        "likes reversed",
                        description="by total likes",
                        value="-likes",
                    ),
                    OpenApiExample(
                        "length",
                        description="by track length",
                        value="length",
                    ),
                    OpenApiExample(
                        "uploaded",
                        description="by date uploaded",
                        value="uploaded",
                    ),
                ],
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ListSongSlugsAPIView(ListBaseSongAPIView):
    serializer_class = ListSongSlugsSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search query",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="sort",
                description="Sorting algorithm",
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        "Default",
                        description="by date added",
                        value=None,
                    ),
                    OpenApiExample(
                        "played",
                        description="by total times played",
                        value="played",
                    ),
                    OpenApiExample(
                        "likes",
                        description="by total likes",
                        value="likes",
                    ),
                    OpenApiExample(
                        "likes reversed",
                        description="by total likes",
                        value="-likes",
                    ),
                    OpenApiExample(
                        "length",
                        description="by track length",
                        value="length",
                    ),
                    OpenApiExample(
                        "uploaded",
                        description="by date uploaded",
                        value="uploaded",
                    ),
                ],
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        songs = self.get_queryset()
        return Response(
            data={
                "songs": songs.values_list("slug", flat=True),
            }
        )


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
        return Song.objects.cache().filter(
            id__in=SongUserRating.objects.cache()
            .filter(user=self.request.user, like=True)
            .values_list("song_id", flat=False)
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
    serializer_class = ListAlbumSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        search = self.request.query_params.get("search", None)
        if search:
            return search_album(search)
        return Album.objects.cache().all()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search query for albums",
                required=False,
                type=str,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RetrieveUpdateDestroyAlbumAPIView(
    LikedSongsContextMixin, generics.RetrieveUpdateDestroyAPIView
):
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = FullAlbumSerializer
    queryset = Album.objects.cache().all()


class ListAuthorsAPIView(generics.ListAPIView):
    serializer_class = ListAuthorSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        search = self.request.query_params.get("search", None)
        if search:
            return search_author(search)
        return Author.objects.cache().all()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search query for authors",
                required=False,
                type=str,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RetrieveUpdateDestroyAuthorAPIView(
    LikedSongsContextMixin, generics.RetrieveUpdateDestroyAPIView
):
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = FullAuthorSerializer
    queryset = Author.objects.cache().all()


class ListenSongAPIView(generics.GenericAPIView):
    serializer_class = ListenSongSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Song.objects.cache()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)

        try:
            song = Song.objects.cache().get(slug=self.request.data.get("song", ""))
        except Song.DoesNotExist:
            return Response(status=404)

        try:
            user_id = self.request.data.get("user_id", None)
            if user_id:
                user_id_int = None
                try:
                    user_id_int = int(user_id)
                except ValueError:
                    ...
                if user_id_int:
                    user = User.objects.cache().get(id=user_id_int)
                    if user != self.request.user:
                        return Response(status=403)
        except User.DoesNotExist:
            ...

        if self.request.user.is_authenticated:
            listen_to_song.apply_async(
                kwargs={
                    "song_id": song.id,
                    "user_id": self.request.user.id,
                    "anon": False,
                },
                countdown=2,
            )
        elif "user_id" in self.request.data:
            listen_to_song.apply_async(
                kwargs={
                    "song_id": song.id,
                    "user_id": self.request.data.get("user_id", None),
                    "anon": True,
                },
                countdown=2,
            )
        else:
            listen_to_song.apply_async(
                kwargs={"song_id": song.id, "user_id": None, "anon": True},
                countdown=2,
            )
        return Response(status=201)


class ListUserListenedSongsAPIView(generics.ListAPIView):
    serializer_class = ListSongSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Song.objects.cache().filter(
            id__in=UserListenHistory.objects.cache()
            .filter(user=self.request.user)
            .values_list("song_id", flat=True)
        )


class CreateAnonMusicUserAPIView(generics.CreateAPIView):
    serializer_class = AnonMusicUserSerializer
    permission_classes = [permissions.AllowAny]


class SearchAllAPIView(LikedSongsContextMixin, generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AllSearchSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="query",
                description="Search query",
                required=True,
                type=str,
            ),
        ],
        responses={
            200: AllSearchSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get("query", "").strip()
        if not query:
            return Response({"songs": [], "albums": [], "authors": []})

        songs = search_song(query)[:10]  # Top 10 songs
        albums = search_album(query)[:5]  # Top 5 albums
        authors = search_author(query)[:5]  # Top 5 authors

        song_serializer = ListSongSerializer(
            songs, many=True, context=self.get_serializer_context()
        )
        album_serializer = ListAlbumSerializer(
            albums, many=True, context=self.get_serializer_context()
        )
        author_serializer = ListAuthorSerializer(
            authors, many=True, context=self.get_serializer_context()
        )

        return Response(
            {
                "songs": song_serializer.data,
                "albums": album_serializer.data,
                "authors": author_serializer.data,
            }
        )
