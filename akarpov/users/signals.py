from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from akarpov.common.tasks import crop_model_image
from akarpov.users.models import User


@receiver(pre_save, sender=User)
def on_change(sender, instance: User, **kwargs):
    if instance.id is None:  # new object will be created
        pass
    else:
        previous = User.objects.get(id=instance.id)
        if previous.image != instance.image and kwargs["update_fields"] != frozenset(
            {"image_cropped"}
        ):
            if instance.image:
                crop_model_image.delay(instance.pk, "users", "User")
            else:
                instance.image_cropped = None
                instance.save()


@receiver(post_save, sender=User)
def post_on_create(sender, instance: User, created, **kwargs):
    if created:
        if instance.image:
            crop_model_image.delay(instance.pk, "users", "User")
