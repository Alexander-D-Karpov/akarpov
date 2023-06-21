from django.contrib import admin

from akarpov.tools.promocodes.models import PromoCode, PromoCodeActivation

admin.site.register(PromoCode)
admin.site.register(PromoCodeActivation)
