from ckeditor_uploader.fields import RichTextUploadingField
from colorfield.fields import ColorField
from django.db import models
from django.db.models import Count
from django.urls import reverse
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from akarpov.common.models import BaseImageModel
from akarpov.tools.shortener.models import ShortLinkModel
from akarpov.users.models import User
from akarpov.users.services.history import UserHistoryModel
from akarpov.utils.string import cleanhtml


class Post(BaseImageModel, ShortLinkModel, UserHistoryModel):
    title = models.CharField(max_length=100, blank=False)
    body = RichTextUploadingField(blank=False)

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")

    post_views = models.IntegerField(default=0)
    rating = models.IntegerField(default=0)
    rating_up = models.IntegerField(default=0)
    rating_down = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)
    public = models.BooleanField(default=True)

    tags = models.ManyToManyField("blog.Tag", related_name="posts")

    def __str__(self):
        return self.title

    def get_rating(self):
        return f"+{self.rating}" if self.rating > 0 else self.rating

    def get_comments(self):
        return self.comments.all()

    def h_tags(self):
        # TODO: add caching here
        tags = (
            Tag.objects.filter(posts__id=self.id)
            .annotate(num_posts=Count("posts"))
            .order_by("-num_posts")
        )
        return tags

    def h_tag(self):
        return self.h_tags().first()

    @property
    def text(self):
        # TODO: add caching here
        return cleanhtml(self.body)

    @property
    @extend_schema_field(serializers.CharField)
    def summary(self):
        body = self.text
        return body[:100] + "..." if len(body) > 100 else ""

    def get_absolute_url(self):
        return reverse("blog:post", kwargs={"slug": self.slug})

    class Meta:
        verbose_name = "Post"
        ordering = ["-created"]

    class SlugMeta:
        slug_length = 3


class Tag(UserHistoryModel):
    name = models.CharField(max_length=20, unique=True)
    color = ColorField(blank=True, default="#FF0000")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("blog:post_list") + f"?tag={self.name}"

    class Meta:
        verbose_name = "Tag"


class PostRating(UserHistoryModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="post_ratings"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="ratings")

    vote_up = models.BooleanField(blank=False)

    def get_absolute_url(self):
        return self.post.get_absolute_url()

    def __str__(self):
        return (
            f"{self.user}'s vote up on {self.post.title}"
            if self.vote_up
            else f"{self.user}'s vote down on {self.post.title}"
        )

    class Meta:
        verbose_name = "Post rating"
        unique_together = ["user", "post"]


class Comment(UserHistoryModel):
    parent = models.ForeignKey("self", blank=True, null=True, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")

    body = models.CharField(max_length=500)
    created = models.DateTimeField(auto_now_add=True)

    rating = models.IntegerField(default=0)

    def get_absolute_url(self):
        return self.post.get_absolute_url() + f"#{self.id}"

    def __str__(self):
        return f"{self.author.username}'s comment on {self.post.title}"

    class Meta:
        verbose_name = "Comment"
        ordering = ["-rating", "-created"]


class CommentRating(UserHistoryModel):
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="ratings"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comment_ratings"
    )

    vote_up = models.BooleanField(blank=False)

    def __str__(self):
        return f"{self.user}'s vote up" if self.vote_up else f"{self.user}'s vote down"

    def get_absolute_url(self):
        return self.comment.get_absolute_url()

    class Meta:
        verbose_name = "Comment rating"
        unique_together = ["comment", "user"]
