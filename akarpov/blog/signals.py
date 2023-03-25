from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from akarpov.blog.models import PostRating, Tag
from akarpov.utils.generators import generate_hex_color


@receiver(pre_save, sender=Tag)
def tag_create(sender, instance: Tag, **kwargs):
    if instance.id is None:
        color = generate_hex_color()
        while Tag.objects.filter(color=color).exists():
            color = generate_hex_color()
        instance.color = color


@receiver(pre_save, sender=PostRating)
def post_rating(sender, instance: PostRating, **kwargs):
    post = instance.post
    if instance.id is None:
        if instance.vote_up:
            post.rating += 1
            post.rating_up += 1
        else:
            post.rating -= 1
            post.rating_down += 1
    else:
        previous = PostRating.objects.get(id=instance.id)
        if previous.vote_up != instance.vote_up:
            if previous.vote_up:
                post.rating -= 2
                post.rating_up -= 1
                post.rating_down += 1
            else:
                post.rating += 2
                post.rating_up += 1
                post.rating_down -= 1
    post.save()


@receiver(pre_delete, sender=PostRating)
def post_rating_delete(sender, instance: PostRating, **kwargs):
    post = instance.post
    if instance.vote_up:
        post.rating -= 1
        post.rating_up -= 1
    else:
        post.rating += 1
        post.rating_down -= 1
    post.save()
