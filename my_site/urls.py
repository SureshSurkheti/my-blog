from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path
from django.views.generic.base import RedirectView

from blog.sitemaps import AuthorSitemap, PostSitemap, TagSitemap

sitemaps = {
    "posts": PostSitemap,
    "tags": TagSitemap,
    "authors": AuthorSitemap,
}


class FaviconView(RedirectView):
    """Browsers request /favicon.ico from the root regardless of link tags.

    Resolved per request rather than at import time, so it works with the
    hashed-filename storage used outside DEBUG.
    """

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return staticfiles_storage.url("favicon.ico")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("favicon.ico", FaviconView.as_view()),
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
