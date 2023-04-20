from django.contrib.sitemaps import Sitemap

from akarpov.users.models import User


class UserSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return User.objects.all()

    def lastmod(self, obj):
        return obj.last_login
