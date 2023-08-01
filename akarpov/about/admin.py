from django.contrib import admin

from akarpov.about.models import FAQ, Project, ProjectChange

admin.site.register(FAQ)
admin.site.register(Project)
admin.site.register(ProjectChange)
