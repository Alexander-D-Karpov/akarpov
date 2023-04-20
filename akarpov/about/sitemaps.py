from django.contrib.sitemaps import Sitemap

from akarpov.about.models import Project


class ProjectsSitemap(Sitemap):
    changefreq = "never"
    priority = 1

    def items(self):
        return Project.objects.all()

    def lastmod(self, obj):
        return obj.modified
