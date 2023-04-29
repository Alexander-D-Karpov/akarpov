from django.contrib import admin

from akarpov.gallery.models import Collection, Image

admin.site.register(Collection)
admin.site.register(Image)
