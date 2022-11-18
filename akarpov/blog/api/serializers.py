from django.shortcuts import get_object_or_404
from rest_framework import serializers

from akarpov.blog.models import Comment, CommentRating, Post, PostRating
from akarpov.blog.services.post import update_comment_rate, update_post_rating
from akarpov.users.api.serializers import UserPublicInfoSerializer


class ListPostSerializer(serializers.ModelSerializer):
    creator = UserPublicInfoSerializer()
    url = serializers.HyperlinkedIdentityField(
        view_name="retrieve_update_delete_post_api", lookup_field="slug"
    )

    class Meta:
        model = Post
        fields = (
            "title",
            "url",
            "creator",
            "post_views",
            "rating",
            "comment_count",
            "date_pub",
        )


class FullPostSerializer(serializers.ModelSerializer):
    creator = UserPublicInfoSerializer(read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "slug",
            "title",
            "body",
            "creator",
            "post_views",
            "rating",
            "rating_count",
            "comment_count",
            "date_pub",
            "edited",
            "image",
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "slug": {"read_only": True},
            "creator": {"read_only": True},
            "post_views": {"read_only": True},
            "rating": {"read_only": True},
            "rating_count": {"read_only": True},
            "comment_count": {"read_only": True},
            "date_pub": {"read_only": True},
            "edited": {"read_only": True},
        }

    def create(self, validated_data):
        return Post.objects.create(
            **validated_data, creator=self.context["request"].user
        )


class CommentSerializer(serializers.ModelSerializer):
    author = UserPublicInfoSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "author", "body", "created", "rating")
        extra_kwargs = {
            "id": {"read_only": True},
            "author": {"read_only": True},
            "created": {"read_only": True},
            "rating": {"read_only": True},
        }

    def create(self, validated_data):
        return Comment.objects.create(
            **validated_data,
            author=self.context["request"].user,
            post=Post.objects.get(
                slug=self.context.get("request")
                .parser_context.get("kwargs")
                .get("slug")
            ),
        )


class UpvoteCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentRating
        fields = ("vote_up",)

    def create(self, validated_data):
        comment = get_object_or_404(
            Comment,
            id=self.context.get("request").parser_context.get("kwargs").get("pk"),
        )
        return update_comment_rate(
            comment, self.context["request"].user, validated_data["vote_up"]
        )


class PostRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostRating
        fields = ("rating",)

    def create(self, validated_data):
        return update_post_rating(
            post=get_object_or_404(
                Post,
                slug=self.context.get("request")
                .parser_context.get("kwargs")
                .get("slug"),
            ),
            user=self.context["request"].user,
            rating=validated_data["rating"],
        )
