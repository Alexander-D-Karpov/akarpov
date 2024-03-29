from django.urls import include, path

app_name = "tools"
urlpatterns = [
    path("qr/", include("akarpov.tools.qr.urls", namespace="qr")),
    path("uuid/", include("akarpov.tools.uuidtools.urls", namespace="uuid")),
    path(
        "promocodes/", include("akarpov.tools.promocodes.urls", namespace="promocodes")
    ),
    path("shortener/", include("akarpov.tools.shortener.urls", namespace="shortener")),
]
