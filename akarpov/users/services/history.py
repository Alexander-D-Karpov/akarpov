from django.db import models
from django.db.models import Model

from akarpov.users.models import User, UserHistory
from akarpov.utils.models import get_app_verbose_name, get_object_name, get_object_user


def create_history_note(user: User, name: str, description: str, obj: Model):
    UserHistory.objects.create(
        type=UserHistory.RecordType.note,
        user=user,
        name=name,
        description=description,
        object=obj,
    )


def create_history_creation_note(user: User, name: str, description: str, obj: Model):
    UserHistory.objects.create(
        type=UserHistory.RecordType.create,
        user=user,
        name=name,
        description=description,
        object=obj,
    )


def create_history_update_note(user: User, name: str, description: str, obj: Model):
    UserHistory.objects.create(
        type=UserHistory.RecordType.update,
        user=user,
        name=name,
        description=description,
        object=obj,
    )


def create_history_delete_note(user: User, name: str, description: str, obj: Model):
    UserHistory.objects.create(
        type=UserHistory.RecordType.delete,
        user=user,
        name=name,
        description=description,
        object=obj,
    )


def create_history_warning_note(user: User, name: str, description: str, obj: Model):
    # TODO: notify user here
    UserHistory.objects.create(
        type=UserHistory.RecordType.warning,
        user=user,
        name=name,
        description=description,
        object=obj,
    )


def create_history_creation_note_on_create(sender, instance, created, **kwargs):
    if created:
        user = get_object_user(instance)
        if user:
            create_history_creation_note(
                user,
                get_app_verbose_name(sender._meta.app_label),
                f"Created {sender._meta.verbose_name.title()} {get_object_name(instance)}",
                instance,
            )


def create_history_update_note_on_update(sender, instance, **kwargs):
    if instance.id:
        user = get_object_user(instance)
        if not kwargs["update_fields"]:
            create_history_update_note(
                user,
                get_app_verbose_name(sender._meta.app_label),
                f"Updated {sender._meta.verbose_name.title()} {get_object_name(instance)}",
                instance,
            )


def create_history_delete_note_on_delete(sender, instance, **kwargs):
    user = get_object_user(instance)
    create_history_delete_note(
        user,
        get_app_verbose_name(sender._meta.app_label),
        f"Deleted {sender._meta.verbose_name.title()} {get_object_name(instance)}",
        instance,
    )


class UserHistoryModel(models.Model):
    """
    creates user history records on model change
    """

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        models.signals.pre_save.connect(
            create_history_update_note_on_update, sender=cls
        )
        models.signals.post_save.connect(
            create_history_creation_note_on_create, sender=cls
        )
        models.signals.post_delete.connect(
            create_history_delete_note_on_delete, sender=cls
        )

    class Meta:
        abstract = True
