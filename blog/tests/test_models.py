from django.test import TestCase
from django.utils import timezone

from blog.models import Comment, Post

from .factories import make_author, make_comment, make_future_post, make_post, make_tag


class SlugTests(TestCase):
    def test_tag_slug_is_derived_from_caption(self):
        self.assertEqual(make_tag("Web Dev").slug, "web-dev")

    def test_author_slug_is_derived_from_full_name(self):
        self.assertEqual(make_author("Grace", "Hopper").slug, "grace-hopper")

    def test_colliding_slugs_get_a_numeric_suffix(self):
        make_author("Grace", "Hopper")
        second = make_author("Grace", "Hopper", email_address="g2@example.com")
        self.assertEqual(second.slug, "grace-hopper-2")

    def test_explicit_slug_is_respected(self):
        self.assertEqual(make_tag("Python", slug="py").slug, "py")


class PublishingTests(TestCase):
    def test_published_at_is_stamped_on_first_publish(self):
        post = make_post(published=True)
        self.assertIsNotNone(post.published_at)

    def test_draft_has_no_published_at(self):
        self.assertIsNone(make_post(published=False).published_at)

    def test_editing_a_published_post_keeps_the_original_date(self):
        post = make_post()
        original = post.published_at
        post.title = "Edited title"
        post.save()
        post.refresh_from_db()
        self.assertEqual(post.published_at, original)

    def test_published_queryset_excludes_drafts_and_future_posts(self):
        live = make_post("Live")
        make_post("Hidden", published=False)
        make_future_post("Later")

        self.assertEqual(list(Post.objects.published()), [live])

    def test_is_published_property(self):
        self.assertTrue(make_post("Yes").is_published)
        self.assertFalse(make_post("No", published=False).is_published)
        self.assertFalse(make_future_post("Soon").is_published)

    def test_default_ordering_is_newest_first(self):
        older = make_post("Older")
        newer = make_post("Newer")
        older.published_at = timezone.now() - timezone.timedelta(days=5)
        older.save()

        self.assertEqual(list(Post.objects.published()), [newer, older])


class SearchQuerySetTests(TestCase):
    def test_matches_title_excerpt_content_and_tag(self):
        tag = make_tag("Testing")
        by_title = make_post("Unicorn stories")
        by_content = make_post("Other", content="A long body mentioning unicorn here.")
        by_tag = make_post("Tagged", tags=[tag])
        make_post("Unrelated", content="Nothing to see in this body at all.")

        self.assertCountEqual(
            Post.objects.published().search("unicorn"), [by_title, by_content]
        )
        self.assertEqual(list(Post.objects.published().search("testing")), [by_tag])

    def test_blank_term_matches_nothing(self):
        make_post()
        self.assertEqual(list(Post.objects.published().search("   ")), [])

    def test_results_are_not_duplicated_by_tag_joins(self):
        tags = [make_tag("Django"), make_tag("Django tips")]
        make_post("Framework notes", tags=tags)
        self.assertEqual(Post.objects.published().search("django").count(), 1)


class UrlAndStringTests(TestCase):
    def test_get_absolute_url(self):
        post = make_post("Hello World")
        self.assertEqual(post.get_absolute_url(), f"/posts/{post.slug}")
        self.assertEqual(make_tag("Hot").get_absolute_url(), "/tags/hot")
        self.assertEqual(make_author("Ada", "L").get_absolute_url(), "/authors/ada-l")

    def test_str_methods(self):
        author = make_author("Ada", "Lovelace")
        post = make_post("Titled", author=author)
        self.assertEqual(str(post), "Titled")
        self.assertEqual(str(author), "Ada Lovelace")
        self.assertEqual(str(make_tag("Hot")), "Hot")
        self.assertEqual(str(make_comment(post, "Grace")), "Grace on Titled")


class CommentTests(TestCase):
    def test_comments_are_newest_first(self):
        post = make_post()
        first = make_comment(post, "First")
        second = make_comment(post, "Second")
        self.assertEqual(list(post.comments.all()), [second, first])

    def test_deleting_a_post_deletes_its_comments(self):
        post = make_post()
        make_comment(post)
        post.delete()
        self.assertEqual(Comment.objects.count(), 0)

    def test_deleting_an_author_keeps_the_posts(self):
        author = make_author()
        post = make_post(author=author)
        author.delete()
        post.refresh_from_db()
        self.assertIsNone(post.author)
