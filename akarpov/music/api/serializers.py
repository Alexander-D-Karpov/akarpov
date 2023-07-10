from rest_framework import serializers

from akarpov.music.models import Album, Author, Song


class AuthorSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(method_name="get_url")

    def get_url(self, obj):
        return obj.get_absolute_url()

    class Meta:
        model = Author
        fields = ["name", "link", "image_cropped", "url"]


class AlbumSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(method_name="get_url")

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
            "id",
            "image",
            "link",
            "length",
            "played",
            "name",
            "file",
            "authors",
            "album",
        ]
