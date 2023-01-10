from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QRConfig(AppConfig):
    verbose_name = _("QR generator")
    name = "akarpov.tools.qr"
