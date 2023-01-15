from django.contrib import admin

from akarpov.files.models import BaseFile, Folder

admin.site.register(BaseFile)
admin.site.register(Folder)
