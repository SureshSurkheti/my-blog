from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse
from django.urls import include, path, reverse
from django.views.generic.base import RedirectView, TemplateView
from django.views.static import serve

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

    /search is endless and thin, /admin/ is not content, and /read-later and
    /credits are both marked noindex anyway.

    The pictures under /files/ are deliberately *not* disallowed: blocking them
    would keep the photographs out of Google Images, which is a large part of
    how a travel post gets found.
    """
    sitemap_url = request.build_absolute_uri(
        reverse("django.contrib.sitemaps.views.sitemap")
    )
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /search",
        "Disallow: /read-later",
        "Disallow: /credits",
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
        # Rendered, not served from disk: it names hashed static files, and
        # only a template can resolve those names.
        "site.webmanifest",
        TemplateView.as_view(
            template_name="site.webmanifest",
            content_type="application/manifest+json",
        ),
        name="webmanifest",
    ),
    path(
        "sitemap.xml",
        sitemap,
        {
            "sitemaps": sitemaps,
            # Django's stock template names each page and nothing else. Ours
            # adds Google's image extension, so a post's photographs are
            # listed with it. Named rather than shadowing "sitemap.xml" in the
            # project template directory, which would override Django's
            # template everywhere without saying so.
            "template_name": "blog/sitemap-with-images.xml",
        },
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("", include("blog.urls")),
]

urlpatterns += [
    path(
        f"{settings.MEDIA_URL.lstrip('/')}<path:path>",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
