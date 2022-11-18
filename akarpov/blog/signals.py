from django.core.files import File
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from akarpov.blog.models import Comment, CommentRating, Post, PostRating
from akarpov.utils.files import crop_image
from akarpov.utils.generators import generate_charset


@receiver(post_save, sender=Post)
def create_post(sender, instance, created, **kwargs):
    if kwargs["update_fields"] != {"post_views"}:
        if created:
            slug = generate_charset(4)
            while Post.objects.filter(slug=slug).exists():
                slug = generate_charset(4)

            instance.slug = slug
            instance.save(update_fields=["slug"])

        if instance.image:
            instance.image_cropped.save(
                instance.image.path.split(".")[0].split("/")[-1] + ".png",
                File(crop_image(instance.image.path, cut_to=(750, 250))),
                save=False,
            )

            post_save.disconnect(create_post, sender=sender)
            instance.save(update_fields=["image_cropped"])
            post_save.connect(create_post, sender=Post)


# comments


@receiver(post_save, sender=Comment)
def create_comment(sender, instance, created, **kwargs):
    if created:
        instance.post.comment_count += 1
        instance.post.save(update_fields=["comment_count"])


@receiver(post_delete, sender=Comment)
def delete_comment(sender, instance, **kwargs):
    instance.post.comment_count -= 1
    instance.post.save(update_fields=["comment_count"])


@receiver(post_delete, sender=CommentRating)
def delete_comment_rating(sender, instance, **kwargs):
    if instance.vote_up:
        instance.comment.rating -= 1
    else:
        instance.comment.rating += 1

    instance.comment.save(update_fields=["rating"])


@receiver(post_delete, sender=PostRating)
def delete_post_rating(sender, instance, **kwargs):
    if instance.post.rating_count != 1:
        rating = instance.post.rating_exactly - instance.rating
        instance.post.rating_exactly -= instance.rating
        instance.post.rating = round(rating / (instance.post.rating_count - 1), 2)
        instance.post.rating_count -= 1
    else:
        instance.post.rating_exactly = 0
        instance.post.rating = 0
        instance.post.rating_count = 0

    instance.post.save(update_fields=["rating_count", "rating_exactly", "rating"])
