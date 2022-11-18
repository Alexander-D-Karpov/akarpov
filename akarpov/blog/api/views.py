from django.db.models import F
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from akarpov.blog.api.serializers import (
    CommentSerializer,
    FullPostSerializer,
    ListPostSerializer,
    PostRateSerializer,
    UpvoteCommentSerializer,
)
from akarpov.blog.models import Comment, CommentRating, Post, PostRating
from akarpov.common.api import SmallResultsSetPagination


class ListPostsApiView(generics.ListAPIView):
    serializer_class = ListPostSerializer
    pagination_class = SmallResultsSetPagination

    permission_classes = [AllowAny]
    queryset = Post.objects.get_queryset().order_by("id")

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class CreatePostApiView(generics.CreateAPIView):
    serializer_class = FullPostSerializer

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class GetUpdateDeletePostApiView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FullPostSerializer
    lookup_field = "slug"

    queryset = Post.objects.all()

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny]
        return [IsAuthenticated]

    authentication_classes = [JWTAuthentication]

    def get_object(self):
        if self.request.method != "GET":
            if super().get_object().creator != self.request.user:
                raise AuthenticationFailed("you are not allowed to access this post")
        return super().get_object()

    def get(self, request, *args, **kwargs):
        post = self.get_object()
        post.post_views = F("post_views") + 1
        post.save(update_fields=["post_views"])

        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class ListCreateCommentApiView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    pagination_class = SmallResultsSetPagination

    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Comment.objects.filter(post__slug=self.kwargs["slug"])

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny]
        return [IsAuthenticated()]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class RetrieveUpdateDeleteCommentApiView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    lookup_field = "pk"

    queryset = Comment.objects.all()
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny]
        return [IsAuthenticated]

    def get_object(self):
        if self.request.method != "GET":
            if super().get_object().author != self.request.user:
                raise AuthenticationFailed("you are not allowed to access this comment")
        return super().get_object()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class CreateDeleteCommentRateApiView(generics.CreateAPIView):
    serializer_class = UpvoteCommentSerializer
    queryset = CommentRating.objects.all()

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        return serializer.save()

    @extend_schema(responses={200: CommentSerializer()})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        comment = CommentSerializer(
            Comment.objects.get(id=self.kwargs["pk"]), context={"request": request}
        )
        return Response(
            data=comment.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(responses={200: CommentSerializer()})
    def delete(self, request, *args, **kwargs):
        CommentRating.objects.filter(
            user=request.user, comment__id=self.kwargs["pk"]
        ).delete()

        comment = CommentSerializer(
            Comment.objects.get(id=self.kwargs["pk"]), context={"request": request}
        )
        return Response(
            data=comment.data,
            status=status.HTTP_200_OK,
        )


class CreateDeletePostRating(generics.CreateAPIView, generics.DestroyAPIView):
    serializer_class = PostRateSerializer
    queryset = PostRating.objects.all()

    def get_post(self):
        return get_object_or_404(Post, slug=self.kwargs["slug"])

    def get_object(self):
        try:
            return PostRating.objects.get(post=self.get_post(), user=self.request.user)
        except PostRating.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @extend_schema(request=PostRateSerializer, responses={200: ListPostSerializer()})
    def post(self, request, *args, **kwargs):
        self.create(request, *args, **kwargs)
        post = ListPostSerializer(self.get_post(), context={"request": request})
        return Response(post.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        post = ListPostSerializer(self.get_post(), context={"request": request})
        return Response(post.data, status=status.HTTP_200_OK)
