from django.core.files import File
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from akarpov.users.models import User
from akarpov.utils.files import crop_image
from akarpov.utils.generators import TokenGenerator


@receiver(post_save, sender=User)
def create_user(sender, instance, created, **kwargs):
    if created:
        instance.is_active = False
        instance.set_password(instance.password)
        instance.save()
        account_activation_token = TokenGenerator()

        mail_subject = "Account activation at akarpov.ru."
        message = render_to_string(
            "email_template.html",
            {
                "user": instance,
                "uid": urlsafe_base64_encode(force_bytes(instance.pk)),
                "token": account_activation_token.make_token(instance),
            },
        )
        send_mail(mail_subject, message, "main@akarpov.ru", [instance.email])

    if instance.image:
        instance.image_cropped.save(
            instance.image.path.split(".")[0].split("/")[-1] + ".png",
            File(crop_image(instance.image.path, cut_to=(250, 250))),
            save=False,
        )

        post_save.disconnect(create_user, sender=sender)
        instance.save(update_fields=["image_cropped"])
        post_save.connect(create_user, sender=User)
