from django.urls import path, include

app_name = "tools"
urlpatterns = [path("qr/", include("akarpov.tools.qr.urls", namespace="qr"))]
