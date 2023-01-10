from django.urls import path

from akarpov.tools.qr.views import qr_create_view

app_name = "qr"
urlpatterns = [path("", qr_create_view, name="create")]
