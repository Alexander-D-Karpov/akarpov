from django.contrib.sitemaps import Sitemap

from akarpov.blog.models import Post


class BlogSitemap(Sitemap):
    changefreq = "never"
    priority = 1

    def items(self):
        return Post.objects.filter(public=True)

    def lastmod(self, obj):
        return obj.edited
