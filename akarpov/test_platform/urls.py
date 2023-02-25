from django.urls import path

from akarpov.test_platform.views import from_create_view

app_name = "test_platform"
urlpatterns = [path("create", from_create_view, name="create")]
