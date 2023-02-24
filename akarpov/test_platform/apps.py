from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TestPlatformConfig(AppConfig):
    name = "akarpov.test_platform"
    verbose_name = _("Test platform")
