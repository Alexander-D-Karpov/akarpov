from akarpov.about.sitemaps import ProjectsSitemap
from akarpov.blog.sitemaps import BlogSitemap
from akarpov.files.sitemaps import FileSitemap
from akarpov.users.sitemaps import UserSitemap

sitemaps = {
    "static": BlogSitemap,
    "projects": ProjectsSitemap,
    "files": FileSitemap,
    "users": UserSitemap,
}
