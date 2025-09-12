from django.db.models import Q
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from akarpov.common.api.serializers import SetUserModelSerializer
from akarpov.music.models import (
    Album,
    AnonMusicUser,
    Author,
    Playlist,
    PlaylistSong,
    Song,
    SongUserRating,
)
from akarpov.users.api.serializers import UserPublicInfoSerializer


class ListAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["name", "slug", "image_cropped"]


class ListAlbumSerializer(serializers.ModelSerializer):
    authors = serializers.SerializerMethodField(method_name="get_authors")

    @extend_schema_field(ListAuthorSerializer(many=True))
    def get_authors(self, obj):
        return ListAuthorSerializer(
            Author.objects.cache().filter(albums__id=obj.id), many=True
        ).data

    class Meta:
        model = Album
        fields = ["name", "slug", "image_cropped", "authors"]


class SongSerializer(serializers.ModelSerializer):
    authors = ListAuthorSerializer(many=True)
    album = ListAlbumSerializer()
    liked = serializers.SerializerMethodField(method_name="get_liked")

    @extend_schema_field(serializers.BooleanField)
    def get_liked(self, obj):
        if "request" in self.context and self.context["request"]:
            if self.context["request"].user.is_authenticated:
                return SongUserRating.objects.filter(
                    song=obj, user=self.context["request"].user, like=True
                ).exists()
        return None

    class Meta:
        model = Song
        fields = [
            "image",
            "link",
            "length",
            "played",
            "name",
            "file",
            "authors",
            "album",
            "liked",
            "meta",
            "volume",
        ]
        extra_kwargs = {
            "slug": {"read_only": True},
            "creator": {"read_only": True},
            "length": {"read_only": True},
            "played": {"read_only": True},
        }


class ListSongSerializer(SetUserModelSerializer):
    album = serializers.SerializerMethodField(method_name="get_album")
    authors = serializers.SerializerMethodField(method_name="get_authors")
    liked = serializers.SerializerMethodField(method_name="get_liked")
    image_cropped = serializers.SerializerMethodField(method_name="get_image")

    @extend_schema_field(serializers.BooleanField)
    def get_liked(self, obj):
        if "likes" in self.context:
            return self.context["likes"]
        if "likes_ids" in self.context:
            return obj.id in self.context["likes_ids"]
        return None

    @extend_schema_field(ListAlbumSerializer)
    def get_album(self, obj):
        if obj.album_id:
            try:
                album = Album.objects.cache().get(id=obj.album_id)
                return ListAlbumSerializer(album).data
            except Album.DoesNotExist:
                return None
        return None

    @extend_schema_field(ListAuthorSerializer(many=True))
    def get_authors(self, obj):
        if obj.authors:
            return ListAuthorSerializer(
                Author.objects.cache().filter(songs__id=obj.id), many=True
            ).data
        return None

    @extend_schema_field(serializers.ImageField)
    def get_image(self, obj):
        img = None
        if obj.image_cropped:
            img = obj.image_cropped
        elif obj.album_id:
            try:
                album = Album.objects.cache().get(id=obj.album_id)
                if album.image_cropped:
                    img = album.image_cropped
            except Album.DoesNotExist:
                pass
        if not img:
            authors = Author.objects.cache().filter(Q(songs__id=obj.id) & ~Q(image=""))
            if authors.exists():
                img = authors.first().image_cropped
        if img:
            return self.context["request"].build_absolute_uri(img.url)
        return None

    class Meta:
        model = Song
        fields = [
            "name",
            "slug",
            "file",
            "image_cropped",
            "length",
            "album",
            "authors",
            "liked",
        ]
        extra_kwargs = {
            "slug": {"read_only": True},
            "image_cropped": {"read_only": True},
            "length": {"read_only": True},
            "album": {"read_only": True},
        }


class PlaylistSerializer(SetUserModelSerializer):
    creator = UserPublicInfoSerializer(read_only=True)
    images = serializers.SerializerMethodField(method_name="get_images")

    @extend_schema_field(serializers.ListField(child=serializers.ImageField()))
    def get_images(self, obj):
        # Get distinct album images from songs
        images = (
            Song.objects.cache()
            .filter(
                playlists__id__in=PlaylistSong.objects.cache()
                .filter(playlist=obj)
                .values("id")
            )
            .values_list("album__image", flat=True)
            .distinct()[:4]
        )
        # Build absolute URI for each image
        images = [
            self.context["request"].build_absolute_uri(image)
            for image in images
            if image
        ]
        return images

    class Meta:
        model = Playlist
        fields = ["name", "length", "slug", "images", "private", "creator"]
        extra_kwargs = {
            "slug": {"read_only": True},
            "creator": {"read_only": True},
            "length": {"read_only": True},
        }


class FullPlaylistSerializer(PlaylistSerializer):
    songs = serializers.SerializerMethodField(method_name="get_songs")
    creator = UserPublicInfoSerializer(read_only=True)

    @extend_schema_field(ListSongSerializer(many=True))
    def get_songs(self, obj):
        return ListSongSerializer(
            Song.objects.cache().filter(playlists__id=obj.id),
            many=True,
            context=self.context,
        ).data

    class Meta:
        model = Playlist
        fields = ["name", "private", "creator", "images", "songs"]
        extra_kwargs = {
            "slug": {"read_only": True},
            "creator": {"read_only": True},
        }


class AddSongToPlaylistSerializer(serializers.ModelSerializer):
    song = serializers.SlugField(write_only=True)
    playlist = serializers.SlugField(write_only=True)

    class Meta:
        model = Playlist
        fields = ["song", "playlist"]
        extra_kwargs = {
            "song": {"write_only": True},
            "playlist": {"write_only": True},
        }

    def validate(self, attrs):
        if not Playlist.objects.filter(slug=attrs["playlist"]).exists():
            raise serializers.ValidationError("Playlist not found")
        if not Song.objects.filter(slug=attrs["song"]).exists():
            raise serializers.ValidationError("Song not found")
        if self.context["create"]:
            if PlaylistSong.objects.filter(
                playlist__slug=attrs["playlist"], song__slug=attrs["song"]
            ).exists():
                raise serializers.ValidationError("Song already in playlist")
        else:
            if not PlaylistSong.objects.filter(
                playlist__slug=attrs["playlist"], song__slug=attrs["song"]
            ).exists():
                raise serializers.ValidationError("Song not in playlist")
        return attrs

    def create(self, validated_data):
        playlist = Playlist.objects.get(slug=validated_data["playlist"])
        song = Song.objects.get(slug=validated_data["song"])
        if not self.context["create"]:
            playlist_song = PlaylistSong.objects.get(
                playlist=playlist, song=song
            ).delete()
        else:
            order = playlist.songs.count()
            playlist_song = playlist.songs.create(song=song, order=order)
        return playlist_song


class ListenSongSerializer(serializers.Serializer):
    song = serializers.SlugField()
    user_id = serializers.CharField(required=False)

    def validate(self, attrs):
        if not Song.objects.filter(slug=attrs["song"]).exists():
            raise serializers.ValidationError("Song not found")

        if "user_id" in attrs and attrs["user_id"]:
            if not AnonMusicUser.objects.filter(id=attrs["user_id"]).exists():
                raise serializers.ValidationError("User not found")
        return attrs


class AnonMusicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnonMusicUser
        fields = ["id"]


class LikeDislikeSongSerializer(serializers.ModelSerializer):
    song = serializers.SlugField()

    class Meta:
        model = SongUserRating
        fields = ["song"]
        extra_kwargs = {
            "song": {"write_only": True},
        }

    def validate(self, attrs):
        if not Song.objects.filter(slug=attrs["song"]).exists():
            raise serializers.ValidationError("Song not found")
        return attrs

    def create(self, validated_data):
        song = Song.objects.get(slug=validated_data["song"])
        user = self.context["request"].user
        is_like_action = self.context["like"]

        try:
            existing_rating = SongUserRating.objects.get(song=song, user=user)

            if is_like_action:
                if existing_rating.like:
                    existing_rating.delete()
                    return None
                else:
                    existing_rating.like = True
                    existing_rating.save()
                    return existing_rating
            else:
                if not existing_rating.like:
                    existing_rating.delete()
                    return None
                else:
                    existing_rating.like = False
                    existing_rating.save()
                    return existing_rating

        except SongUserRating.DoesNotExist:
            return SongUserRating.objects.create(
                song=song, user=user, like=is_like_action
            )


class ListSongSlugsSerializer(serializers.Serializer):
    slugs = serializers.ListField(child=serializers.SlugField())


class ListPlaylistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playlist
        fields = ["name", "slug", "private"]
        extra_kwargs = {
            "slug": {"read_only": True},
            "private": {"read_only": True},
        }


class FullAlbumSerializer(serializers.ModelSerializer):
    songs = ListSongSerializer(many=True, read_only=True)
    artists = serializers.SerializerMethodField("get_artists")

    @extend_schema_field(ListAuthorSerializer(many=True))
    def get_artists(self, obj):
        artists = []
        qs = Author.objects.cache().filter(
            songs__id__in=obj.songs.cache().all().values("id").distinct()
        )
        for artist in qs:
            if artist not in artists:
                artists.append(artist)

        return ListAuthorSerializer(
            artists,
            many=True,
        ).data

    class Meta:
        model = Album
        fields = ["name", "link", "image", "songs", "artists", "meta"]
        extra_kwargs = {
            "link": {"read_only": True},
            "image": {"read_only": True},
        }


class FullAuthorSerializer(serializers.ModelSerializer):
    songs = ListSongSerializer(many=True, read_only=True)
    albums = serializers.SerializerMethodField(method_name="get_albums")

    @extend_schema_field(ListAlbumSerializer(many=True))
    def get_albums(self, obj):
        qs = Album.objects.cache().filter(
            songs__id__in=obj.songs.cache().all().values("id").distinct()
        )
        albums = []
        for album in qs:
            # TODO: rewrite to filter
            if album not in albums:
                albums.append(album)

        return ListAlbumSerializer(
            albums,
            many=True,
        ).data

    class Meta:
        model = Author
        fields = ["name", "link", "image", "songs", "albums", "meta"]
        extra_kwargs = {
            "link": {"read_only": True},
            "image": {"read_only": True},
        }


class AllSearchSerializer(serializers.Serializer):
    songs = serializers.SerializerMethodField(method_name="get_songs")
    authors = serializers.SerializerMethodField(method_name="get_authors")
    albums = serializers.SerializerMethodField(method_name="get_albums")

    @extend_schema_field(ListSongSerializer(many=True))
    def get_songs(self, obj):
        return ListSongSerializer(
            Song.objects.cache().search(obj["query"]).to_queryset()[:10],
            many=True,
            context=self.context,
        ).data

    @extend_schema_field(ListAuthorSerializer(many=True))
    def get_authors(self, obj):
        return ListAuthorSerializer(
            Author.objects.cache().search(obj["query"]).to_queryset()[:10], many=True
        ).data

    @extend_schema_field(ListAlbumSerializer(many=True))
    def get_albums(self, obj):
        return ListAlbumSerializer(
            Album.objects.cache().search(obj["query"]).to_queryset()[:10], many=True
        ).data
