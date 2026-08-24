"""Moving between posts: the back link and the newer/older neighbours."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .factories import make_future_post, make_post


class NeighbourTests(TestCase):
    def setUp(self):
        # Oldest to newest, one day apart.
        self.first = make_post("First")
        self.second = make_post("Second")
        self.third = make_post("Third")
        now = timezone.now()
        for offset, post in enumerate((self.first, self.second, self.third)):
            post.published_at = now - timezone.timedelta(days=10 - offset)
            post.save()

    def test_middle_post_links_both_ways(self):
        self.assertEqual(self.second.get_newer_post(), self.third)
        self.assertEqual(self.second.get_older_post(), self.first)

    def test_newest_post_has_nothing_newer(self):
        self.assertIsNone(self.third.get_newer_post())
        self.assertEqual(self.third.get_older_post(), self.second)

    def test_oldest_post_has_nothing_older(self):
        self.assertIsNone(self.first.get_older_post())
        self.assertEqual(self.first.get_newer_post(), self.second)

    def test_drafts_are_never_neighbours(self):
        draft = make_post("Draft copy", published=False)
        draft.published_at = self.second.published_at + timezone.timedelta(hours=1)
        draft.save()

        self.assertEqual(self.second.get_newer_post(), self.third)

    def test_future_posts_are_never_neighbours(self):
        make_future_post("Scheduled")
        self.assertIsNone(self.third.get_newer_post())

    def test_a_draft_has_no_neighbours_of_its_own(self):
        draft = make_post("Unpublished", published=False)
        self.assertIsNone(draft.get_newer_post())
        self.assertIsNone(draft.get_older_post())

    def test_posts_sharing_a_publish_date_are_not_skipped(self):
        """Everything migrated from the old `date` field shares a timestamp."""
        stamp = timezone.now() - timezone.timedelta(days=5)
        a = make_post("Same day A")
        b = make_post("Same day B")
        c = make_post("Same day C")
        for post in (a, b, c):
            post.published_at = stamp
            post.save()

        # Walking older-wards from the newest must visit every post exactly once.
        from blog.models import Post

        walk, seen = [], Post.objects.published().first()
        while seen is not None and len(walk) < 20:
            walk.append(seen.pk)
            seen = seen.get_older_post()

        self.assertEqual(len(walk), len(set(walk)))
        self.assertEqual(len(walk), Post.objects.published().count())


class NavigationRenderingTests(TestCase):
    def setUp(self):
        self.older = make_post("Older one")
        self.newer = make_post("Newer one")
        self.older.published_at = timezone.now() - timezone.timedelta(days=3)
        self.older.save()

    def test_back_link_to_the_list_is_present(self):
        response = self.client.get(self.newer.get_absolute_url())
        self.assertContains(response, "All posts")
        self.assertContains(response, f'href="{reverse("posts-page")}"')

    def test_neighbour_links_are_rendered(self):
        response = self.client.get(self.older.get_absolute_url())

        self.assertEqual(response.context["newer_post"], self.newer)
        self.assertIsNone(response.context["older_post"])
        self.assertContains(response, self.newer.get_absolute_url())
        self.assertContains(response, "Keep reading")
        self.assertContains(response, "Newer post")

    def test_a_missing_neighbour_is_omitted_rather_than_shown_empty(self):
        response = self.client.get(self.older.get_absolute_url())
        # Only one card, and no placeholder text where the other would be.
        self.assertEqual(response.content.decode().count("post-nav__card"), 1)
        self.assertNotContains(response, "Older post")

    def test_the_card_shows_the_neighbour_title_and_date(self):
        response = self.client.get(self.older.get_absolute_url())
        self.assertContains(response, self.newer.title)
        self.assertContains(response, "post-nav__date")

    def test_rel_attributes_match_the_direction(self):
        response = self.client.get(self.older.get_absolute_url())
        self.assertContains(response, 'rel="prev"')

    def test_the_panel_is_hidden_when_a_post_has_no_neighbours(self):
        self.newer.delete()
        response = self.client.get(self.older.get_absolute_url())

        self.assertNotContains(response, 'id="post-nav"')
        # The back link at the top is still the way out.
        self.assertContains(response, "All posts")

    def test_draft_preview_still_renders_the_navigation(self):
        draft = make_post("Draft copy", published=False)
        User.objects.create_user("editor", password="pw12345!", is_staff=True)
        self.client.login(username="editor", password="pw12345!")

        response = self.client.get(draft.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["newer_post"])
        self.assertIsNone(response.context["older_post"])
        self.assertNotContains(response, 'id="post-nav"')
