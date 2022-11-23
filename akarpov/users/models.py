from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, ImageField, TextField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from akarpov.utils.files import user_file_upload_mixin


class User(AbstractUser):
    """
    Default custom user model for akarpov.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    #: First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    about = TextField(_("Description"), blank=True, max_length=100)
    image = ImageField(upload_to=user_file_upload_mixin, blank=True)
    image_cropped = ImageField(upload_to="cropped/", blank=True)
    first_name = None  # type: ignore
    last_name = None  # type: ignore

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})
