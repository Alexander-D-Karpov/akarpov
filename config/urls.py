from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views import defaults as default_views
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from akarpov.about.views import about_view, list_faq
from akarpov.tools.shortener.views import redirect_view
from config.sitemaps import sitemaps

urlpatterns = [
    path(
        "home",
        cache_page(600)(TemplateView.as_view(template_name="pages/home.html")),
        name="home",
    ),
    re_path(r"^robots\.txt", include("robots.urls")),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("health/", include("health_check.urls")),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("akarpov.users.urls", namespace="users")),
    path("about", cache_page(600)(about_view), name="about"),
    path("faq/", list_faq, name="faq"),
    path("about/", include("akarpov.about.urls", namespace="about")),
    path("files/", include("akarpov.files.urls", namespace="files")),
    path("music/", include("akarpov.music.urls", namespace="music")),
    path("forms/", include("akarpov.test_platform.urls", namespace="forms")),
    path("tools/", include("akarpov.tools.urls", namespace="tools")),
    path("gallery/", include("akarpov.gallery.urls", namespace="gallery")),
    path("ckeditor/", include("ckeditor_uploader.urls")),
    path("accounts/", include("allauth.urls")),
    path("", include("akarpov.blog.urls", namespace="blog")),
    path("<str:slug>", redirect_view, name="short_url"),
    # Your stuff: custom urls includes go here
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("config.api_router", namespace="api")),
    # DRF auth token
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-redoc-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="swagger",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="api-redoc-schema"),
        name="redoc",
    ),
]

if settings.USE_DEBUG_TOOLBAR:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
