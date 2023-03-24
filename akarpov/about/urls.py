from django.urls import path

from . import views

app_name = "about"

urlpatterns = [
    path("", views.about_view, name="about"),
    path("<int:pk>", views.project_view, name="project"),
]
