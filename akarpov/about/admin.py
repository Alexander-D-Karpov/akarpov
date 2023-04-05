from django.contrib import admin

from akarpov.about.models import Project, ProjectChange

admin.site.register(Project)
admin.site.register(ProjectChange)
