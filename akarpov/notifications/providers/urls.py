from django.urls import include, path

app_name = "notifications"
urlpatterns = [
    path(
        "site/", include("akarpov.notifications.providers.site.urls", namespace="site")
    ),
]
