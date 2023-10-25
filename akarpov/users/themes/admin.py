from django.contrib import admin

from akarpov.users.themes.models import Theme


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    ...
