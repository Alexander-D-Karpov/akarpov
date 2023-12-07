from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from akarpov.common.api.serializers import SetUserModelSerializer
from akarpov.music.models import Album, Author, Playlist, Song
from akarpov.users.api.serializers import UserPublicInfoSerializer


class AuthorSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(method_name="get_url")

    @extend_schema_field(serializers.URLField)
    def get_url(self, obj):
        return obj.get_absolute_url()

    class Meta:
        model = Author
        fields = ["name", "link", "image_cropped", "url"]


class AlbumSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(method_name="get_url")

    @extend_schema_field(serializers.URLField)
    def get_url(self, obj):
        return obj.get_absolute_url()

    class Meta:
        model = Album
        fields = ["name", "link", "image_cropped", "url"]


class SongSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True)
    album = AlbumSerializer()

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
        ]
        extra_kwargs = {
            "slug": {"read_only": True},
            "creator": {"read_only": True},
            "length": {"read_only": True},
            "played": {"read_only": True},
        }


class ListSongSerializer(SetUserModelSerializer):
    album = serializers.CharField(source="album.name", read_only=True)
    liked = serializers.SerializerMethodField(method_name="get_liked")

    def get_liked(self, obj):
        return obj.id in self.context["likes_ids"]

    class Meta:
        model = Song
        fields = ["name", "slug", "file", "image_cropped", "length", "album"]
        extra_kwargs = {
            "slug": {"read_only": True},
            "image_cropped": {"read_only": True},
            "length": {"read_only": True},
            "album": {"read_only": True},
        }


class PlaylistSerializer(SetUserModelSerializer):
    creator = UserPublicInfoSerializer()

    class Meta:
        model = Playlist
        fields = ["name", "slug", "private", "creator"]
        extra_kwargs = {
            "slug": {"read_only": True},
            "creator": {"read_only": True},
        }


class FullPlaylistSerializer(serializers.ModelSerializer):
    songs = ListSongSerializer(many=True, read_only=True)
    creator = UserPublicInfoSerializer(read_only=True)

    class Meta:
        model = Playlist
        fields = ["name", "private", "creator", "songs"]
        extra_kwargs = {
            "slug": {"read_only": True},
            "creator": {"read_only": True},
        }
