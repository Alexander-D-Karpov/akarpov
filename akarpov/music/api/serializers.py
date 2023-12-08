from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from akarpov.common.api.serializers import SetUserModelSerializer
from akarpov.music.models import (
    Album,
    Author,
    Playlist,
    PlaylistSong,
    Song,
    SongUserRating,
)
from akarpov.users.api.serializers import UserPublicInfoSerializer


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["name", "slug", "image_cropped"]


class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = ["name", "slug", "image_cropped"]


class SongSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True)
    album = AlbumSerializer()
    liked = serializers.SerializerMethodField(method_name="get_liked")

    @extend_schema_field(serializers.BooleanField)
    def get_liked(self, obj):
        if "request" in self.context:
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
        ]
        extra_kwargs = {
            "slug": {"read_only": True},
            "creator": {"read_only": True},
            "length": {"read_only": True},
            "played": {"read_only": True},
        }


class ListSongSerializer(SetUserModelSerializer):
    album = AlbumSerializer(read_only=True)
    authors = AuthorSerializer(many=True, read_only=True)
    liked = serializers.SerializerMethodField(method_name="get_liked")

    @extend_schema_field(serializers.BooleanField)
    def get_liked(self, obj):
        if "likes" in self.context:
            return self.context["likes"]
        if "likes_ids" in self.context:
            return obj.id in self.context["likes_ids"]
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

    class Meta:
        model = Playlist
        fields = ["name", "length", "slug", "private", "creator"]
        extra_kwargs = {
            "slug": {"read_only": True},
            "creator": {"read_only": True},
            "length": {"read_only": True},
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


class AddSongToPlaylistSerializer(serializers.ModelSerializer):
    song = serializers.SlugField()
    playlist = serializers.SlugField()

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
        if self.context["like"]:
            if SongUserRating.objects.filter(
                song=song, user=self.context["request"].user
            ).exists():
                song_user_rating = SongUserRating.objects.get(
                    song=song, user=self.context["request"].user
                )
                if song_user_rating.like:
                    song_user_rating.delete()
                else:
                    song_user_rating.like = True
                    song_user_rating.save()
            else:
                song_user_rating = SongUserRating.objects.create(
                    song=song, user=self.context["request"].user, like=True
                )
        else:
            if SongUserRating.objects.filter(
                song=song, user=self.context["request"].user
            ).exists():
                song_user_rating = SongUserRating.objects.get(
                    song=song, user=self.context["request"].user
                )
                if not song_user_rating.like:
                    song_user_rating.delete()
                else:
                    song_user_rating.like = False
                    song_user_rating.save()
            else:
                song_user_rating = SongUserRating.objects.create(
                    song=song, user=self.context["request"].user, like=False
                )
        return song_user_rating


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

    class Meta:
        model = Album
        fields = ["name", "link", "image", "songs"]
        extra_kwargs = {
            "link": {"read_only": True},
            "image": {"read_only": True},
        }


class FullAuthorSerializer(serializers.ModelSerializer):
    songs = ListSongSerializer(many=True, read_only=True)

    class Meta:
        model = Author
        fields = ["name", "link", "image", "songs"]
        extra_kwargs = {
            "link": {"read_only": True},
            "image": {"read_only": True},
        }
