from django.urls import include, path

from akarpov.tools.api.views import RetrieveAPIUrlAPIView

app_name = "tools"

urlpatterns = [
    path("<str:path>", RetrieveAPIUrlAPIView.as_view(), name="path"),
    path("qr/", include("akarpov.tools.qr.api.urls", namespace="qr")),
]
