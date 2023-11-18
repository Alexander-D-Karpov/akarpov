from rest_framework import serializers

from akarpov.gallery.models import Image


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = (
            "slug",
            "image",
            "collection",
            "public",
            "image_cropped",
            "created",
            "modified",
        )
        extra_kwargs = {
            "slug": {"read_only": True},
            "collection": {"write_only": True},
            "image_cropped": {"read_only": True},
            "created": {"read_only": True},
            "modified": {"read_only": True},
        }
