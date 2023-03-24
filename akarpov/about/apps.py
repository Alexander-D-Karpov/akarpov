from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AboutConfig(AppConfig):
    name = "akarpov.about"
    verbose_name = _("About me app")
