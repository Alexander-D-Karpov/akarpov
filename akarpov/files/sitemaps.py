from django.contrib.sitemaps import Sitemap

from akarpov.files.models import File


class FileSitemap(Sitemap):
    changefreq = "never"
    priority = 0.8

    def items(self):
        return File.objects.filter(private=False)

    def lastmod(self, obj):
        return obj.modified
