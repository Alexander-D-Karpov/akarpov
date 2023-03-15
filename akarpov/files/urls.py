from django.urls import path

from akarpov.files.views import files_view, folder_view

app_name = "files"
urlpatterns = [
    path("<str:slug>", files_view, name="view"),
    path("f/<str:slug>", folder_view, name="folder"),
]
