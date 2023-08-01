from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny

from akarpov.blog.api.serializers import (
    CommentSerializer,
    FullPostSerializer,
    PostSerializer,
)
from akarpov.blog.models import Post
from akarpov.blog.services import get_main_rating_posts
from akarpov.common.api import StandardResultsSetPagination


class ListMainPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return get_main_rating_posts()


class ListPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Post.objects.all()


class GetPost(generics.RetrieveAPIView):
    serializer_class = FullPostSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        post = get_object_or_404(Post, slug=self.kwargs["slug"])
        post.post_views += 1
        post.save(update_fields=["post_views"])
        return post


class ListCommentsSerializer(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        post = get_object_or_404(Post, slug=self.kwargs["slug"])
        return post.comments.filter(parent__isnull=True)
