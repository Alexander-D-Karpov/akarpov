from django.db.models.signals import pre_save
from django.dispatch import receiver

from akarpov.users.models import User


@receiver(pre_save, sender=User)
def user_create(sender, instance: User, **kwargs):
    if instance.id is None:
        # give user some space on file share on register
        instance.left_file_upload += 100 * 1024 * 1024
