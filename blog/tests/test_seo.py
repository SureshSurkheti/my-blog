"""Canonical, Open Graph, Twitter, structured data, robots and headings."""

import json
import re
import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from .factories import make_author, make_image_file, make_post, make_tag

MEDIA_ROOT = tempfile.mkdtemp(prefix="blog-seo-media-")


class CanonicalTests(TestCase):
    def test_every_page_declares_a_canonical_url(self):
        post = make_post("Canonical")
        for url in (
            reverse("starting-page"),
            reverse("posts-page"),
            post.get_absolute_url(),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'rel="canonical"')
                self.assertContains(response, f"http://testserver{url}")

    def test_pagination_self_canonicalises(self):
        for i in range(9):
            make_post(f"Post {i}")

        response = self.client.get(reverse("posts-page"), {"page": 2})

        self.assertContains(response, "/posts?page=2")

    def test_tracking_parameters_are_dropped_from_the_canonical(self):
        response = self.client.get(reverse("posts-page"), {"utm_source": "newsletter"})

        canonical = re.search(
            r'rel="canonical" href="([^"]+)"', response.content.decode()
        ).group(1)
        self.assertNotIn("utm_source", canonical)
        self.assertTrue(canonical.endswith("/posts"))


class SocialCardTests(TestCase):
    def setUp(self):
        self.post = make_post(
            "Shared post",
            excerpt="A short summary for the card.",
            author=make_author("Ada", "Lovelace"),
            tags=[make_tag("Japan")],
        )

    def test_post_declares_article_open_graph_tags(self):
        response = self.client.get(self.post.get_absolute_url())

        self.assertContains(response, 'property="og:type" content="article"')
        self.assertContains(response, 'property="og:title" content="Shared post"')
        self.assertContains(response, "A short summary for the card.")
        self.assertContains(response, 'property="article:published_time"')
        self.assertContains(response, 'property="article:modified_time"')
        self.assertContains(response, 'property="article:tag" content="Japan"')

    def test_lists_are_website_type(self):
        response = self.client.get(reverse("posts-page"))
        self.assertContains(response, 'property="og:type" content="website"')

    def test_twitter_card_is_declared(self):
        response = self.client.get(self.post.get_absolute_url())
        self.assertContains(
            response, 'name="twitter:card" content="summary_large_image"'
        )
        self.assertContains(response, 'name="twitter:image"')

    def test_image_url_is_absolute(self):
        """Crawlers reject relative og:image values."""
        response = self.client.get(self.post.get_absolute_url())
        image = re.search(
            r'property="og:image" content="([^"]+)"', response.content.decode()
        ).group(1)
        self.assertTrue(image.startswith("http://testserver/"))

    def test_a_post_without_a_picture_falls_back_to_the_site_icon(self):
        response = self.client.get(self.post.get_absolute_url())
        self.assertContains(response, "icon-512.png")


class StructuredDataTests(TestCase):
    @staticmethod
    def _schema(body):
        """Every JSON-LD object on the page, keyed by @type."""
        payload = json.loads(
            re.search(
                r'<script type="application/ld\+json">(.*?)</script>', body, re.S
            ).group(1)
        )
        blocks = payload if isinstance(payload, list) else [payload]
        return {block["@type"]: block for block in blocks}

    def test_post_carries_blogposting_schema(self):
        author = make_author("Ada", "Lovelace")
        post = make_post("Structured", author=author, tags=[make_tag("Japan")])

        body = self.client.get(post.get_absolute_url()).content.decode()
        payload = self._schema(body)["BlogPosting"]

        self.assertEqual(payload["headline"], "Structured")
        self.assertEqual(payload["author"]["name"], "Ada Lovelace")
        self.assertIn("datePublished", payload)
        self.assertIn("dateModified", payload)
        self.assertEqual(payload["keywords"], ["Japan"])

    def test_post_carries_a_breadcrumb_trail(self):
        # Google renders this in place of the raw URL under a search result.
        post = make_post("Structured", slug="structured")

        body = self.client.get(post.get_absolute_url()).content.decode()
        crumbs = self._schema(body)["BreadcrumbList"]["itemListElement"]

        self.assertEqual(
            [c["name"] for c in crumbs], ["Home", "All posts", "Structured"]
        )
        self.assertEqual([c["position"] for c in crumbs], [1, 2, 3])
        for crumb in crumbs:
            with self.subTest(name=crumb["name"]):
                self.assertTrue(crumb["item"].startswith("http"))

    def test_the_trail_ends_on_the_page_it_is_served_from(self):
        post = make_post("Structured", slug="structured")

        body = self.client.get(post.get_absolute_url()).content.decode()
        crumbs = self._schema(body)["BreadcrumbList"]["itemListElement"]

        self.assertTrue(crumbs[-1]["item"].endswith(post.get_absolute_url()))

    def test_homepage_carries_website_schema_with_search(self):
        body = self.client.get(reverse("starting-page")).content.decode()
        payload = self._schema(body)["WebSite"]

        self.assertIn("search?q={search_term_string}", json.dumps(payload))

    def test_script_content_cannot_break_out_of_the_tag(self):
        post = make_post("Breakout", excerpt="</script><script>alert(1)</script>")
        body = self.client.get(post.get_absolute_url()).content.decode()
        self.assertNotIn("</script><script>alert(1)", body)


class IndexingRulesTests(TestCase):
    def test_robots_txt_points_at_the_sitemap(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        body = response.content.decode()
        self.assertIn("Sitemap: http://testserver/sitemap.xml", body)
        self.assertIn("Disallow: /admin/", body)
        self.assertIn("Disallow: /search", body)

    def test_search_results_are_not_indexed(self):
        response = self.client.get(reverse("search-page"), {"q": "anything"})
        self.assertContains(response, 'name="robots" content="noindex,follow"')

    def test_saved_page_is_not_indexed(self):
        response = self.client.get(reverse("read-later"))
        self.assertContains(response, 'name="robots" content="noindex,follow"')

    def test_published_posts_are_indexable(self):
        post = make_post("Indexable")
        self.assertNotContains(self.client.get(post.get_absolute_url()), "noindex")

    def test_sitemap_includes_the_homepage_and_archive(self):
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("<loc>http://testserver/</loc>", body)
        self.assertIn("<loc>http://testserver/posts</loc>", body)


class HeadingStructureTests(TestCase):
    def test_each_page_has_exactly_one_h1(self):
        post = make_post("Headings", tags=[make_tag("Japan")])
        for url in (
            reverse("starting-page"),
            reverse("posts-page"),
            post.get_absolute_url(),
            reverse("read-later"),
            reverse("search-page"),
            "/tags/japan",
        ):
            with self.subTest(url=url):
                body = self.client.get(url).content.decode()
                self.assertEqual(body.count("<h1"), 1, f"{url} h1 count")

    def test_the_post_h1_is_the_post_title(self):
        post = make_post("The actual subject")
        body = self.client.get(post.get_absolute_url()).content.decode()

        heading = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S).group(1).strip()
        self.assertEqual(heading, "The actual subject")

    def test_the_site_name_is_not_a_heading(self):
        body = self.client.get(reverse("posts-page")).content.decode()
        header = body[body.index("<header") : body.index("</header>")]
        self.assertNotIn("<h1", header)


class LayoutStabilityTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    @override_settings(MEDIA_ROOT=MEDIA_ROOT)
    def test_images_declare_their_intrinsic_size(self):
        """width/height let the browser reserve space, avoiding layout shift."""
        post = make_post("With picture", image=make_image_file(size=(1200, 800)))

        response = self.client.get(reverse("posts-page"))

        self.assertEqual(post.image_width, 1200)
        self.assertEqual(post.image_height, 800)
        self.assertContains(response, 'width="1200"')
        self.assertContains(response, 'height="800"')
