from allauth.account.signals import (
    email_added,
    email_changed,
    email_removed,
    password_reset,
    user_logged_in,
)
from allauth.socialaccount.signals import social_account_added
from django.contrib.auth import user_logged_out
from django.db.models.signals import pre_save
from django.dispatch import receiver

from akarpov.users.models import User
from akarpov.users.services.history import (
    create_history_note,
    create_history_warning_note,
)


@receiver(pre_save, sender=User)
def user_create(sender, instance: User, **kwargs):
    if instance.id is None:
        # give user some space on file share on register
        instance.left_file_upload += 100 * 1024 * 1024


@receiver(user_logged_in)
def user_logged_in(request, user, **kwargs):
    create_history_note(user, "User", "log in", user)


@receiver(user_logged_out)
def user_logged_out(request, user, **kwargs):
    create_history_note(user, "User", "log out", user)


@receiver(password_reset)
def user_password_reset(request, user, **kwargs):
    create_history_warning_note(user, "User", "password reset", user)


@receiver(email_changed)
def user_email_change(request, user, from_email_address, to_email_address, **kwargs):
    create_history_warning_note(
        user, "User", f"user email changed to {to_email_address}", user
    )


@receiver(email_added)
def user_email_add(request, user, email_address, **kwargs):
    create_history_warning_note(user, "User", f"email {email_address} added", user)


@receiver(email_removed)
def user_email_remove(request, user, email_address, **kwargs):
    create_history_warning_note(user, "User", f"email {email_address} removed", user)


@receiver(social_account_added)
def user_account_add(request, sociallogin, **kwargs):
    create_history_warning_note(
        request.user, "User", f"added {sociallogin.provider} account", request.user
    )
