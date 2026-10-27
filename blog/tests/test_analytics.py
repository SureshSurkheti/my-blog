"""Counting readers without a script, a cookie, or a third party."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import DailyCount

from .factories import make_post

HUMAN = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131"


class CountingTests(TestCase):
    def setUp(self):
        self.post = make_post("Beppu", slug="beppu")
        self.url = self.post.get_absolute_url()

    def views_of(self, key, kind=DailyCount.PAGE):
        row = DailyCount.objects.filter(kind=kind, key=key).first()
        return row.views if row else 0

    def test_a_page_view_is_counted(self):
        self.client.get(self.url, HTTP_USER_AGENT=HUMAN)

        self.assertEqual(self.views_of(self.url), 1)

    def test_a_second_view_increments_the_same_row(self):
        # One row per page per day is the whole storage design; a row per
        # visit would grow without limit.
        for _ in range(3):
            self.client.get(self.url, HTTP_USER_AGENT=HUMAN)

        self.assertEqual(self.views_of(self.url), 3)
        self.assertEqual(DailyCount.objects.filter(kind=DailyCount.PAGE).count(), 1)

    def test_the_uptime_pinger_is_not_the_most_popular_page(self):
        self.client.get("/", HTTP_USER_AGENT="keep-awake-worker")
        self.client.get("/", HTTP_USER_AGENT="UptimeRobot/2.0")

        self.assertEqual(self.views_of("/"), 0)

    def test_search_engines_are_not_counted_as_readers(self):
        self.client.get(self.url, HTTP_USER_AGENT="Googlebot/2.1 (+http://google.com/bot)")

        self.assertEqual(self.views_of(self.url), 0)

    def test_a_request_with_no_user_agent_is_not_counted(self):
        self.client.get(self.url)

        self.assertEqual(self.views_of(self.url), 0)

    def test_the_owner_reading_their_own_site_is_not_counted(self):
        staff = get_user_model().objects.create_user(
            "suresh", password="x", is_staff=True
        )
        self.client.force_login(staff)

        self.client.get(self.url, HTTP_USER_AGENT=HUMAN)

        self.assertEqual(self.views_of(self.url), 0)

    def test_a_missing_page_is_not_counted(self):
        self.client.get("/posts/not-a-real-post", HTTP_USER_AGENT=HUMAN)

        self.assertEqual(DailyCount.objects.count(), 0)

    def test_assets_and_machine_endpoints_are_not_counted(self):
        for path in ("/robots.txt", "/sitemap.xml", "/feed/rss"):
            with self.subTest(path=path):
                self.client.get(path, HTTP_USER_AGENT=HUMAN)

        self.assertEqual(DailyCount.objects.filter(kind=DailyCount.PAGE).count(), 0)

    def test_a_post_request_is_not_counted(self):
        self.client.post(reverse("read-later"), {"post_id": self.post.id},
                         HTTP_USER_AGENT=HUMAN)

        self.assertEqual(DailyCount.objects.count(), 0)


class ReferrerTests(TestCase):
    def setUp(self):
        self.post = make_post("Beppu", slug="beppu")
        self.url = self.post.get_absolute_url()

    def hosts(self):
        return list(
            DailyCount.objects.filter(kind=DailyCount.REFERRER).values_list("key", flat=True)
        )

    def test_the_sending_site_is_recorded(self):
        self.client.get(self.url, HTTP_USER_AGENT=HUMAN,
                        HTTP_REFERER="https://www.google.com/search?q=beppu+onsen")

        self.assertEqual(self.hosts(), ["www.google.com"])

    def test_only_the_host_is_kept(self):
        # The full URL can carry search terms and session ids. None of that is
        # needed to know that Google sent someone.
        self.client.get(self.url, HTTP_USER_AGENT=HUMAN,
                        HTTP_REFERER="https://x.com/path?token=secret-value")

        self.assertNotIn("secret-value", str(self.hosts()))
        self.assertEqual(self.hosts(), ["x.com"])

    def test_moving_around_the_site_is_not_a_referral(self):
        self.client.get(self.url, HTTP_USER_AGENT=HUMAN,
                        HTTP_REFERER="https://blog.sureshsurkheti.com/posts")

        self.assertEqual(self.hosts(), [])

    def test_a_direct_visit_records_no_referrer(self):
        self.client.get(self.url, HTTP_USER_AGENT=HUMAN)

        self.assertEqual(self.hosts(), [])


class StatsPageTests(TestCase):
    def setUp(self):
        self.post = make_post("Beppu", slug="beppu")

    def test_a_stranger_gets_a_404_not_a_login_redirect(self):
        # A redirect would confirm the address exists.
        self.assertEqual(self.client.get(reverse("stats")).status_code, 404)

    def test_a_signed_in_reader_who_is_not_staff_also_gets_404(self):
        user = get_user_model().objects.create_user("reader", password="x")
        self.client.force_login(user)

        self.assertEqual(self.client.get(reverse("stats")).status_code, 404)

    def test_the_owner_sees_the_numbers(self):
        self.client.get(self.post.get_absolute_url(), HTTP_USER_AGENT=HUMAN)
        staff = get_user_model().objects.create_user("suresh", password="x", is_staff=True)
        self.client.force_login(staff)

        response = self.client.get(reverse("stats"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Beppu")

    def test_it_is_kept_out_of_search_results(self):
        staff = get_user_model().objects.create_user("suresh", password="x", is_staff=True)
        self.client.force_login(staff)

        self.assertContains(self.client.get(reverse("stats")), "noindex")

    def test_robots_disallows_it(self):
        self.assertContains(self.client.get("/robots.txt"), "Disallow: /stats")

    def test_it_is_not_in_the_sitemap(self):
        self.assertNotContains(self.client.get("/sitemap.xml"), "/stats")


class ResilienceTests(TestCase):
    def test_a_counting_failure_never_costs_the_reader_the_page(self):
        """The counter is a convenience; the page is the product."""
        from unittest import mock

        post = make_post("Beppu", slug="beppu")
        with mock.patch("blog.analytics.record", side_effect=RuntimeError("boom")):
            response = self.client.get(post.get_absolute_url(), HTTP_USER_AGENT=HUMAN)

        self.assertEqual(response.status_code, 200)


class StorageShapeTests(TestCase):
    def test_two_pages_on_one_day_are_two_rows(self):
        first = make_post("One", slug="one")
        second = make_post("Two", slug="two")

        for url in (first.get_absolute_url(), second.get_absolute_url()):
            self.client.get(url, HTTP_USER_AGENT=HUMAN)

        self.assertEqual(DailyCount.objects.filter(kind=DailyCount.PAGE).count(), 2)

    def test_the_same_page_cannot_have_two_rows_for_one_day(self):
        from django.db import IntegrityError, transaction

        post = make_post("Beppu", slug="beppu")
        today = timezone.localdate()
        DailyCount.objects.create(kind=DailyCount.PAGE, key=post.get_absolute_url(),
                                  day=today, views=1)

        with self.assertRaises(IntegrityError), transaction.atomic():
            DailyCount.objects.create(kind=DailyCount.PAGE, key=post.get_absolute_url(),
                                      day=today, views=1)


class CostTests(TestCase):
    """This runs on every request, so its cost is the whole site's cost."""

    def setUp(self):
        self.post = make_post("Beppu", slug="beppu")
        self.url = self.post.get_absolute_url()

    def _queries(self, **extra):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as captured:
            self.client.get(self.url, HTTP_USER_AGENT=HUMAN, **extra)
        return [q["sql"] for q in captured]

    def test_a_repeat_view_costs_a_single_statement(self):
        # The row exists on every view but the first, so the common path must
        # be one UPDATE and never a read followed by a write.
        self._queries()  # the first view creates the row
        before = len(self._queries())
        counting = [q for q in self._queries() if "dailycount" in q.lower()]

        self.assertEqual(len(counting), 1)
        self.assertIn("UPDATE", counting[0].upper())

    def test_a_referral_costs_one_more_and_no_reads(self):
        self._queries(HTTP_REFERER="https://news.ycombinator.com/")
        counting = [
            q for q in self._queries(HTTP_REFERER="https://news.ycombinator.com/")
            if "dailycount" in q.lower()
        ]

        self.assertEqual(len(counting), 2)
        for sql in counting:
            self.assertIn("UPDATE", sql.upper())

    def test_an_ignored_request_touches_the_table_not_at_all(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as captured:
            self.client.get(self.url, HTTP_USER_AGENT="UptimeRobot/2.0")

        self.assertEqual(
            [q for q in captured.captured_queries if "dailycount" in q["sql"].lower()], []
        )


class BackupTests(TestCase):
    def test_readership_is_kept_out_of_the_content_fixture(self):
        """`make backup` dumps the blog app, which now includes counts.

        Left in, the fixture grows with every day of traffic, and the
        loaddata on a rebuilt database would write stale counts over whatever
        the live site had recorded since.
        """
        from pathlib import Path

        from django.conf import settings

        makefile = (Path(settings.BASE_DIR) / "Makefile").read_text()
        dump = makefile[makefile.index("dumpdata blog") :]

        self.assertIn("--exclude blog.DailyCount", dump[:200])


class StatsRenderingTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            "suresh", password="x", is_staff=True
        )
        self.client.force_login(self.staff)

    def test_both_ends_of_the_date_axis_are_labelled(self):
        # {{ series.last }} silently rendered nothing: Django resolves a key,
        # then an attribute, then an integer index, and a list has none of
        # those called "last".
        make_post("Beppu", slug="beppu")
        DailyCount.objects.create(
            kind=DailyCount.PAGE, key="/posts/beppu",
            day=timezone.localdate(), views=3,
        )

        body = self.client.get(reverse("stats")).content.decode()
        axis = body[body.index('class="stats__axis"') :]
        axis = axis[: axis.index("</p>")]

        self.assertEqual(axis.count("<span>"), 2)
        for span in axis.split("<span>")[1:]:
            self.assertTrue(span[: span.index("</span>")].strip())

    def test_an_empty_site_says_so_rather_than_drawing_nothing(self):
        self.assertContains(self.client.get(reverse("stats")), "first reader")
