from django.urls import path

from akarpov.test_platform.views import form_create_view, form_view

app_name = "test_platform"
urlpatterns = [
    path("create", form_create_view, name="create"),
    path("<str:slug>", form_view, name="view"),
]
