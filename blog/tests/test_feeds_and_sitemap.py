from django.test import TestCase
from django.urls import reverse

from .factories import make_author, make_future_post, make_post, make_tag


class FeedTests(TestCase):
    def setUp(self):
        self.author = make_author("Ada", "Lovelace")
        self.post = make_post("Feed Me", author=self.author)
        make_post("Hidden draft", published=False)
        make_future_post("Scheduled")

    def test_rss_feed_lists_published_posts_only(self):
        response = self.client.get(reverse("post-feed-rss"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("application/rss+xml", response["Content-Type"])
        body = response.content.decode()
        self.assertIn("Feed Me", body)
        self.assertNotIn("Hidden draft", body)
        self.assertNotIn("Scheduled", body)

    def test_atom_feed_works(self):
        response = self.client.get(reverse("post-feed-atom"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/atom+xml", response["Content-Type"])
        self.assertIn("Feed Me", response.content.decode())

    def test_feed_entries_link_to_the_post(self):
        body = self.client.get(reverse("post-feed-rss")).content.decode()
        self.assertIn(self.post.get_absolute_url(), body)

    def test_feed_is_discoverable_from_the_homepage(self):
        response = self.client.get(reverse("starting-page"))
        self.assertContains(response, 'type="application/rss+xml"')


class SitemapTests(TestCase):
    def test_sitemap_lists_published_posts_tags_and_authors(self):
        post = make_post("Mapped")
        make_post("Draft copy", published=False)
        tag = make_tag("Django")
        author = make_author("Grace", "Hopper")

        response = self.client.get("/sitemap.xml")
        body = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn(post.get_absolute_url(), body)
        self.assertIn(tag.get_absolute_url(), body)
        self.assertIn(author.get_absolute_url(), body)
        self.assertNotIn("/posts/draft-copy", body)


class FeedVisibilityTests(TestCase):
    """The feeds exist and are discoverable, but aren't advertised in the footer."""

    def test_the_footer_does_not_link_them(self):
        body = self.client.get(reverse("starting-page")).content.decode()
        footer = body[body.index("site-footer") :]

        self.assertNotIn(">RSS<", footer)
        self.assertNotIn(">Atom<", footer)

    def test_they_stay_discoverable_in_the_head(self):
        body = self.client.get(reverse("starting-page")).content.decode()
        head = body[: body.index("</head>")]

        self.assertIn('type="application/rss+xml"', head)
        self.assertIn('type="application/atom+xml"', head)

    def test_the_urls_still_work(self):
        make_post("Still fed")
        for name in ("post-feed-rss", "post-feed-atom"):
            with self.subTest(feed=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
