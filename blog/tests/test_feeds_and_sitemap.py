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
        tag = make_tag("Django")
        author = make_author("Grace", "Hopper")
        post = make_post("Mapped", tags=[tag], author=author)
        make_post("Draft copy", published=False)

        response = self.client.get("/sitemap.xml")
        body = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn(post.get_absolute_url(), body)
        self.assertIn(tag.get_absolute_url(), body)
        self.assertIn(author.get_absolute_url(), body)
        self.assertNotIn("/posts/draft-copy", body)


class EmptyPageSitemapTests(TestCase):
    """A tag or author page with nothing on it must not be advertised.

    Tagging a draft creates the tag immediately, so between writing a post and
    publishing it the tag exists but its page is blank. Listing that in the
    sitemap invites a crawler to index an empty page, which is worse for the
    site than the tag simply not being listed yet.
    """

    def test_a_tag_carried_only_by_a_draft_is_left_out(self):
        tag = make_tag("Festivals")
        make_post("Unpublished", published=False, tags=[tag])

        body = self.client.get("/sitemap.xml").content.decode()

        self.assertNotIn(tag.get_absolute_url(), body)

    def test_an_author_with_only_drafts_is_left_out(self):
        author = make_author("Unpublished", "Writer")
        make_post("Still writing", published=False, author=author)

        body = self.client.get("/sitemap.xml").content.decode()

        self.assertNotIn(author.get_absolute_url(), body)

    def test_a_scheduled_post_does_not_count_as_published_yet(self):
        tag = make_tag("Embargoed")
        make_future_post("Next week", tags=[tag])

        body = self.client.get("/sitemap.xml").content.decode()

        self.assertNotIn(tag.get_absolute_url(), body)

    def test_publishing_one_post_is_enough_to_list_the_tag(self):
        tag = make_tag("Oita")
        make_post("A draft too", published=False, tags=[tag])
        make_post("Live one", tags=[tag])

        body = self.client.get("/sitemap.xml").content.decode()

        self.assertIn(tag.get_absolute_url(), body)

    def test_a_tag_is_listed_once_however_many_posts_carry_it(self):
        # ``posts__in`` is a join, so without .distinct() the tag would appear
        # once per matching post.
        tag = make_tag("Nature")
        make_post("First", tags=[tag])
        make_post("Second", tags=[tag])

        body = self.client.get("/sitemap.xml").content.decode()

        self.assertEqual(body.count(tag.get_absolute_url()), 1)


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
