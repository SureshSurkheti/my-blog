from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse
from django.urls import include, path, reverse
from django.views.generic.base import RedirectView

from blog.sitemaps import (
    AuthorSitemap,
    PostSitemap,
    StaticViewSitemap,
    TagSitemap,
)

sitemaps = {
    "pages": StaticViewSitemap,
    "posts": PostSitemap,
    "tags": TagSitemap,
    "authors": AuthorSitemap,
}


def robots_txt(request):
    """Point crawlers at the sitemap and keep them out of what can't help them.

    /search is endless and thin; /admin/ and /files/ are not content.
    """
    sitemap_url = request.build_absolute_uri(
        reverse("django.contrib.sitemaps.views.sitemap")
    )
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /search",
        "Disallow: /read-later",
        "Allow: /",
        "",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


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
    path("robots.txt", robots_txt, name="robots-txt"),
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
