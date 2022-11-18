from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from akarpov.users.models import User
from akarpov.utils.files import user_file_upload_mixin


class Post(models.Model):
    """Model to store user's posts"""

    title = models.CharField(max_length=120, db_index=True)
    slug = models.SlugField(max_length=150, blank=False, unique=True)
    body = models.TextField(blank=False, db_index=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")

    post_views = models.IntegerField(default=0)
    rating = models.FloatField(
        default=0, validators=[MaxValueValidator(5), MinValueValidator(0)]
    )
    rating_exactly = models.IntegerField(default=0)
    rating_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)

    date_pub = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)

    image = models.ImageField(upload_to=user_file_upload_mixin, blank=True)
    image_cropped = models.ImageField(upload_to="cropped/", blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["id"]


class PostRating(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="post_ratings"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="ratings")

    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    def __str__(self):
        return f"{self.user.username}'s rating {self.rating} on {self.post.title}"

    class Meta:
        unique_together = ["user", "post"]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")

    body = models.CharField(max_length=500)
    created = models.DateTimeField(auto_now_add=True)

    rating = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.author.username}'s comment on {self.post.title}"

    class Meta:
        ordering = ["-rating"]


class CommentRating(models.Model):
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="ratings"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comment_ratings"
    )

    vote_up = models.BooleanField(blank=False)

    def __str__(self):
        return f"{self.user}'s vote up" if self.vote_up else f"{self.user}'s vote down"

    class Meta:
        unique_together = ["comment", "user"]
