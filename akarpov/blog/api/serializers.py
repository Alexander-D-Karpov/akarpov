from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from akarpov.blog.models import Comment, Post, Tag
from akarpov.common.api.serializers import RecursiveField
from akarpov.users.api.serializers import UserPublicInfoSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name", "color"]


class PostSerializer(serializers.ModelSerializer):
    creator = UserPublicInfoSerializer()
    main_tag = serializers.SerializerMethodField(method_name="get_h_tag")
    url = serializers.HyperlinkedIdentityField(
        view_name="api:blog:post", lookup_field="slug"
    )
    short_link = serializers.URLField(source="get_short_link")

    @extend_schema_field(TagSerializer)
    def get_h_tag(self, obj):
        return TagSerializer(many=False).to_representation(instance=obj.h_tags()[0])

    class Meta:
        model = Post
        fields = [
            "title",
            "url",
            "main_tag",
            "image_cropped",
            "summary",
            "creator",
            "post_views",
            "rating",
            "comment_count",
            "short_link",
            "created",
            "edited",
        ]
        extra_kwargs = {
            "url": {"view_name": "api:blog:post", "lookup_field": "slug"},
        }


class FullPostSerializer(PostSerializer):
    """note: body is returned as html for format"""

    tags = TagSerializer(many=True)
    comments = serializers.HyperlinkedIdentityField(
        view_name="api:blog:post_comments", lookup_field="slug"
    )
    short_link = serializers.URLField(source="get_short_link")

    class Meta:
        model = Post
        fields = [
            "title",
            "image",
            "tags",
            "summary",
            "creator",
            "post_views",
            "rating",
            "comment_count",
            "comments",
            "short_link",
            "created",
            "edited",
        ]

        extra_kwargs = {
            "fio": {"required": False},
            "username": {"required": False},
            "is_agent": {"read_only": True},
            "form": {"read_only": True},
        }


class CommentSerializer(serializers.ModelSerializer):
    author = UserPublicInfoSerializer()
    children = RecursiveField(many=True)

    class Meta:
        model = Comment
        fields = ["author", "body", "created", "rating", "children"]
