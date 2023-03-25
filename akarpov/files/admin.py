from django.contrib import admin

from akarpov.files.models import File, Folder

admin.site.register(File)
admin.site.register(Folder)
