from django.urls import include, path

app_name = "tools"
urlpatterns = [path("qr/", include("akarpov.tools.qr.urls", namespace="qr"))]
