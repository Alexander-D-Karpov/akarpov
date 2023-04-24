from django.contrib import admin

from akarpov.files.models import File, FileInTrash, FileReport, Folder

admin.site.register(File)
admin.site.register(Folder)
admin.site.register(FileInTrash)
admin.site.register(FileReport)
