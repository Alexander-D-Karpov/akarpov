from django.urls import path

from akarpov.notifications.providers.site.api.views import ListNotificationsAPIView

app_name = "notifications:site"
urlpatterns = [
    path("", ListNotificationsAPIView.as_view(), name="list"),
]
