from django.urls import path

from . import views

app_name = "gallery"

urlpatterns = [
    path("", views.ListCreateImageAPIView.as_view(), name="list-create-all"),
]
