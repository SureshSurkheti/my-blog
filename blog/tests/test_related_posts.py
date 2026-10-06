"""Links between posts on the same subject, rather than only by date."""

import re

from django.test import TestCase
from django.urls import reverse

from blog.models import Post, Tag

from .factories import make_future_post, make_post, make_tag


class RelatedPostsTests(TestCase):
    def setUp(self):
        self.onsen = make_tag("Onsen")
        self.oita = make_tag("Oita")
        self.food = make_tag("Food")
        self.post = make_post("Beppu", slug="beppu", tags=[self.onsen, self.oita])

    def test_a_post_sharing_a_tag_is_offered(self):
        other = make_post("Kurokawa", slug="kurokawa", tags=[self.onsen])

        self.assertIn(other, self.post.related_posts())

    def test_a_post_sharing_nothing_is_not(self):
        make_post("Yatai", slug="yatai", tags=[self.food])

        self.assertEqual(list(self.post.related_posts()), [])

    def test_more_shared_tags_ranks_higher(self):
        # The whole point of ordering by overlap: two tags in common is a
        # closer match than one, whatever the dates say.
        one = make_post("One tag", slug="one", tags=[self.onsen])
        two = make_post("Two tags", slug="two", tags=[self.onsen, self.oita])

        self.assertEqual(list(self.post.related_posts())[0], two)
        self.assertIn(one, self.post.related_posts())

    def test_a_post_never_offers_itself(self):
        make_post("Kurokawa", slug="kurokawa", tags=[self.onsen])

        self.assertNotIn(self.post, self.post.related_posts())

    def test_drafts_are_not_offered(self):
        draft = make_post("Unpublished", slug="draft", published=False, tags=[self.onsen])

        self.assertNotIn(draft, self.post.related_posts())

    def test_a_scheduled_post_is_not_offered_early(self):
        future = make_future_post("Next week", slug="next-week", tags=[self.onsen])

        self.assertNotIn(future, self.post.related_posts())

    def test_a_post_with_no_tags_has_nothing_related(self):
        bare = make_post("Untagged", slug="untagged")

        self.assertEqual(list(bare.related_posts()), [])

    def test_the_limit_is_respected(self):
        for n in range(5):
            make_post(f"Onsen {n}", slug=f"onsen-{n}", tags=[self.onsen])

        self.assertEqual(len(self.post.related_posts(limit=3)), 3)

    def test_sharing_two_tags_does_not_list_a_post_twice(self):
        # Without .distinct() the join returns one row per matching tag.
        twice = make_post("Both", slug="both", tags=[self.onsen, self.oita])

        self.assertEqual(list(self.post.related_posts()).count(twice), 1)

    def test_excluded_posts_are_left_out(self):
        neighbour = make_post("Neighbour", slug="neighbour", tags=[self.onsen])

        self.assertNotIn(neighbour, self.post.related_posts(exclude=(neighbour,)))

    def test_exclude_tolerates_none(self):
        # The view passes the newer and older posts, either of which is None
        # at the ends of the archive.
        make_post("Kurokawa", slug="kurokawa", tags=[self.onsen])

        self.assertEqual(len(self.post.related_posts(exclude=(None, None))), 1)


class RelatedPostsPageTests(TestCase):
    def setUp(self):
        self.onsen = make_tag("Onsen")
        self.post = make_post("Beppu", slug="beppu", tags=[self.onsen])

    def test_the_section_appears_when_there_is_something_to_show(self):
        # Four posts, not two: the newer and older neighbours are excluded
        # from this section, so with only one other post there is correctly
        # nothing left to show.
        make_post("Yufuin", slug="yufuin", tags=[self.onsen])
        make_post("Kurokawa", slug="kurokawa", tags=[self.onsen])
        make_post("Kannawa", slug="kannawa", tags=[self.onsen])

        response = self.client.get(reverse("post-detail-page", args=["beppu"]))

        self.assertContains(response, "More like this")

    def test_the_section_is_absent_when_there_is_nothing(self):
        response = self.client.get(reverse("post-detail-page", args=["beppu"]))

        self.assertNotContains(response, "More like this")

    def test_a_post_is_not_offered_under_two_headings_at_once(self):
        # It would otherwise show up both as "More like this" and as the
        # newer or older post immediately below.
        other = make_post("Kurokawa", slug="kurokawa", tags=[self.onsen])

        body = self.client.get(reverse("post-detail-page", args=["beppu"])).content.decode()

        self.assertEqual(body.count(other.get_absolute_url()), 1)


    def test_the_only_other_post_is_left_to_keep_reading(self):
        """With one other post it is the neighbour, so this section is empty.

        Not a bug: it would otherwise appear twice on a short page, once under
        each heading. On a site with more posts the neighbours are a small
        slice of what shares a tag.
        """
        make_post("Kurokawa", slug="kurokawa", tags=[self.onsen])

        response = self.client.get(reverse("post-detail-page", args=["beppu"]))

        self.assertNotContains(response, "More like this")
        self.assertContains(response, "Keep reading")

class RelatedPostsQueryTests(TestCase):
    def test_reading_each_result_costs_no_further_queries(self):
        """Every card prints the post's first tag and the template reaches for
        its author, both of which are one query per card without a prefetch.

        An earlier version of this test compared the page's query count with
        four posts against twelve and asserted they matched. They always
        matched: the list is capped at three cards, so the count could not
        grow whatever the prefetch did, and removing .with_related() left it
        passing. This touches the attributes directly instead.
        """
        onsen, oita = make_tag("Onsen"), make_tag("Oita")
        post = make_post("Beppu", slug="beppu", tags=[onsen, oita])
        for n in range(5):
            make_post(f"Other {n}", slug=f"other-{n}", tags=[onsen, oita])

        related = list(post.related_posts())
        self.assertEqual(len(related), 3)

        with self.assertNumQueries(0):
            for found in related:
                list(found.tags.all())
                str(found.author)

    def test_a_post_without_tags_never_runs_the_related_lookup(self):
        # Reading the tags costs one query on an instance nobody prefetched;
        # the point is that the second, expensive one is skipped entirely.
        bare = make_post("Untagged", slug="untagged")
        make_post("Something else", slug="else", tags=[make_tag("Onsen")])

        with self.assertNumQueries(1):
            list(bare.related_posts())


class CardImageWeightTests(TestCase):
    """Card pictures are 6.5rem wide and must not pull the full upload.

    The Beppu post was 539 KB, of which 396 KB was two card thumbnails
    fetching their originals into a 104px box.
    """

    def setUp(self):
        from .factories import make_image_file

        onsen = make_tag("Onsen")
        self.post = make_post("Beppu", slug="beppu", tags=[onsen])
        for n in range(3):
            make_post(f"Other {n}", slug=f"other-{n}", tags=[onsen],
                      image=make_image_file(f"other-{n}.jpg", size=(1600, 1000)))

    def test_every_card_picture_offers_narrow_variants(self):
        body = self.client.get(self.post.get_absolute_url()).content.decode()
        section = body[body.index("post-nav__grid"):]

        for tag in re.findall(r"<img[^>]*>", section):
            with self.subTest(tag=tag[:60]):
                self.assertIn("srcset=", tag)

    def test_the_cards_tell_the_browser_how_small_they_are(self):
        # A srcset without sizes makes the browser assume full viewport width
        # and pick the largest rung anyway, which is the bug all over again.
        body = self.client.get(self.post.get_absolute_url()).content.decode()
        section = body[body.index("post-nav__grid"):]

        for tag in re.findall(r"<img[^>]*srcset[^>]*>", section):
            with self.subTest(tag=tag[:60]):
                self.assertIn("5.5rem", tag)
                self.assertIn("6.5rem", tag)
