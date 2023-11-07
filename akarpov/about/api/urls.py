from django.urls import path

from akarpov.about.api.views import PingAPIView

app_name = "about"

urlpatterns = [path("ping", PingAPIView.as_view(), name="ping")]
