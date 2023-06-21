from django.urls import path

from akarpov.tools.promocodes.views import activate_promo_code

app_name = "promocodes"

urlpatterns = [
    path("", activate_promo_code, name="activate"),
]
