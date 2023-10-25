from django.urls import path

from akarpov.users.themes.views import CreateFormView

app_name = "themes"
urlpatterns = [
    path("create", CreateFormView.as_view(), name="create"),
]
