"""Counting what gets read, without a third party and without cookies.

Render's dashboard reports CPU, memory and bandwidth — how hard the server is
working, not which post anybody read. Google Search Console answers who
arrived from a search, but says nothing about the rest.

This counts page views in the site's own database. There is no client-side
script, so it costs the reader nothing and cannot be blocked; nothing
identifies a person, so there is no cookie banner to add and no data to leak.

What it gives up in exchange is unique visitors: without a cookie or a
fingerprint, ten views are ten views whether that is ten people or one person
reloading. For a blog this size that is the right trade.

Rows are aggregated per day rather than stored per request, so the table
grows by the number of pages read in a day, not the number of reads — about
five thousand rows a year at this size rather than one per visit.
"""

from urllib.parse import urlparse

from django.db.models import F
from django.utils import timezone

# Paths that are not reading. /admin is work, /static and /files are assets,
# and the rest are either machine-facing or the owner's own tools.
IGNORED_PREFIXES = (
    "/admin",
    "/static",
    "/files",
    "/favicon",
    "/robots.txt",
    "/sitemap.xml",
    "/feed",
    "/site.webmanifest",
    "/stats",
)

# The keep-alive pings would otherwise be the most popular page on the site.
IGNORED_AGENTS = (
    "keep-awake-worker",
    "uptimerobot",
    "pingdom",
    "better uptime",
    "betteruptime",
    "curl/",
    "wget",
    "python-requests",
    "go-http-client",
    "headlesschrome",
)

# Search engines are not readers either, but they are worth separating from
# the noise above rather than pretending they do not exist.
CRAWLER_HINTS = ("bot", "crawler", "spider", "slurp", "bingpreview")


def should_count(request, response):
    """True when this looks like a person reading a page of the site."""
    if request.method != "GET" or response.status_code != 200:
        return False

    if not response.get("Content-Type", "").startswith("text/html"):
        return False

    path = request.path
    if any(path.startswith(prefix) for prefix in IGNORED_PREFIXES):
        return False

    agent = request.META.get("HTTP_USER_AGENT", "").lower()
    if not agent:
        return False
    if any(hint in agent for hint in IGNORED_AGENTS):
        return False
    if any(hint in agent for hint in CRAWLER_HINTS):
        return False

    # Staff reading their own site would otherwise dominate the numbers.
    user = getattr(request, "user", None)
    return not (user and user.is_authenticated and user.is_staff)


def referrer_host(request):
    """The site a reader arrived from, or None for a direct visit.

    Only the host is kept. The full URL can carry search terms and session
    identifiers, and none of that is needed to know that Google sent someone.
    """
    referrer = request.META.get("HTTP_REFERER", "")
    if not referrer:
        return None
    host = (urlparse(referrer).hostname or "").lower()
    if not host or host.endswith("sureshsurkheti.com"):
        return None  # moving around the site is not a referral
    return host[:120]


def record(request, response):
    """Add one to today's count for this page, and for where it came from."""
    from blog.models import DailyCount  # imported late: models import settings

    if not should_count(request, response):
        return

    today = timezone.localdate()
    _bump(DailyCount.PAGE, request.path[:200], today)

    host = referrer_host(request)
    if host:
        _bump(DailyCount.REFERRER, host, today)


def _bump(kind, key, day):
    from blog.models import DailyCount

    # UPDATE first: the row exists on every view but the first, so this is one
    # statement in the common case and never reads before writing.
    updated = DailyCount.objects.filter(kind=kind, key=key, day=day).update(
        views=F("views") + 1
    )
    if not updated:
        DailyCount.objects.get_or_create(
            kind=kind, key=key, day=day, defaults={"views": 1}
        )


class AnalyticsMiddleware:
    """Counts after the response is built, so it never delays the page.

    A failure here must never cost a reader the page they asked for, so
    anything that goes wrong is swallowed: a missing count is not worth a 500.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            record(request, response)
        except Exception:  # noqa: BLE001 - a counter must not break the site
            pass
        return response
