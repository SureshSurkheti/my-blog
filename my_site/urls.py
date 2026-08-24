from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from blog.sitemaps import AuthorSitemap, PostSitemap, TagSitemap

sitemaps = {
    "posts": PostSitemap,
    "tags": TagSitemap,
    "authors": AuthorSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("", include("blog.urls")),
]

if settings.DEBUG:
    # In production the web server serves uploads; Django only does it locally.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
