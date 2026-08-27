import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from blog.models import Comment

from .factories import (
    make_author,
    make_comment,
    make_future_post,
    make_image_file,
    make_post,
    make_tag,
)

SETTINGS_TWO_PER_PAGE = {
    "title": "Test Blog",
    "description": "Testing.",
    "posts_per_page": 2,
    "latest_posts_count": 2,
}


class StartingPageTests(TestCase):
    def test_shows_only_the_configured_number_of_latest_posts(self):
        for i in range(4):
            make_post(f"Post {i}")

        with self.settings(BLOG_SETTINGS=SETTINGS_TWO_PER_PAGE):
            response = self.client.get(reverse("starting-page"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["posts"]), 2)

    def test_drafts_and_future_posts_are_hidden(self):
        make_post("Visible")
        make_post("Draft copy", published=False)
        make_future_post("Scheduled")

        response = self.client.get(reverse("starting-page"))

        self.assertContains(response, "Visible")
        self.assertNotContains(response, "Draft copy")
        self.assertNotContains(response, "Scheduled")

    def test_renders_without_posts(self):
        response = self.client.get(reverse("starting-page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No posts published yet")


class AllPostsTests(TestCase):
    def test_pagination(self):
        for i in range(5):
            make_post(f"Post {i}")

        with self.settings(BLOG_SETTINGS=SETTINGS_TWO_PER_PAGE):
            first = self.client.get(reverse("posts-page"))
            third = self.client.get(reverse("posts-page"), {"page": 3})
            over = self.client.get(reverse("posts-page"), {"page": 9})

        self.assertEqual(len(first.context["posts"]), 2)
        self.assertEqual(first.context["paginator"].num_pages, 3)
        self.assertEqual(len(third.context["posts"]), 1)
        self.assertEqual(over.status_code, 404)

    def test_uses_a_bounded_number_of_queries(self):
        author = make_author()
        tags = [make_tag("One"), make_tag("Two")]
        for i in range(5):
            make_post(f"Post {i}", author=author, tags=tags)

        # select_related/prefetch_related keep this flat as posts are added:
        # count, tag sidebar, the page of posts, and one prefetch for tags.
        with self.assertNumQueries(4):
            self.client.get(reverse("posts-page"))


class SinglePostTests(TestCase):
    def setUp(self):
        self.post = make_post("Readable", author=make_author())

    def test_renders_a_published_post(self):
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Readable")

    def test_unknown_slug_returns_404_not_a_server_error(self):
        response = self.client.get("/posts/no-such-post")
        self.assertEqual(response.status_code, 404)

    def test_draft_is_hidden_from_visitors(self):
        draft = make_post("Secret", published=False)
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)

    def test_staff_can_preview_a_draft(self):
        draft = make_post("Secret", published=False)
        User.objects.create_user("editor", password="pw12345!", is_staff=True)
        self.client.login(username="editor", password="pw12345!")

        response = self.client.get(draft.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Draft preview")

    def test_non_staff_login_still_cannot_see_drafts(self):
        draft = make_post("Secret", published=False)
        User.objects.create_user("reader", password="pw12345!")
        self.client.login(username="reader", password="pw12345!")

        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)

    def test_post_without_an_image_renders(self):
        no_image = make_post("Imageless", image=None)
        self.assertEqual(self.client.get(no_image.get_absolute_url()).status_code, 200)

    def test_markdown_in_the_body_is_rendered(self):
        post = make_post("Formatted", content="Some **bold** text right here.")
        response = self.client.get(post.get_absolute_url())
        self.assertContains(response, "<strong>bold</strong>")


class CommentSubmissionTests(TestCase):
    def setUp(self):
        self.post = make_post("Commentable")

    def test_valid_comment_is_saved_and_redirects(self):
        response = self.client.post(
            self.post.get_absolute_url(),
            {"user_name": "Ada", "user_email": "ada@example.com", "text": "Great post"},
        )

        self.assertRedirects(response, self.post.get_absolute_url())
        self.assertEqual(self.post.comments.count(), 1)

    def test_invalid_comment_is_rejected_and_redisplays_errors(self):
        response = self.client.post(
            self.post.get_absolute_url(),
            {"user_name": "Ada", "user_email": "not-an-email", "text": "ok"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Comment.objects.count(), 0)
        self.assertTrue(response.context["comment_form"].errors)

    def test_existing_comments_are_listed(self):
        make_comment(self.post, "Grace", text="Loved this one.")
        response = self.client.get(self.post.get_absolute_url())
        self.assertContains(response, "Loved this one.")
        self.assertContains(response, "1 Comment")


class TagAndAuthorPageTests(TestCase):
    def test_tag_page_lists_only_that_tags_posts(self):
        tag = make_tag("Django")
        tagged = make_post("Tagged post", tags=[tag])
        make_post("Untagged post")

        response = self.client.get(tag.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["posts"]), [tagged])
        self.assertEqual(response.context["tag"], tag)

    def test_author_page_lists_only_that_authors_posts(self):
        author = make_author("Ada", "Lovelace")
        mine = make_post("Mine", author=author)
        make_post(
            "Theirs", author=make_author("Grace", "Hopper", email_address="g@e.com")
        )

        response = self.client.get(author.get_absolute_url())

        self.assertEqual(list(response.context["posts"]), [mine])

    def test_unknown_tag_or_author_returns_404(self):
        self.assertEqual(self.client.get("/tags/nope").status_code, 404)
        self.assertEqual(self.client.get("/authors/nobody").status_code, 404)

    def test_tag_page_hides_drafts(self):
        tag = make_tag("Django")
        make_post("Draft one", published=False, tags=[tag])
        response = self.client.get(tag.get_absolute_url())
        self.assertEqual(list(response.context["posts"]), [])


class SearchTests(TestCase):
    def test_finds_matching_posts(self):
        match = make_post("Unicorn stories")
        make_post("Something else", content="Body with no keyword in it here.")

        response = self.client.get(reverse("search-page"), {"q": "unicorn"})

        self.assertEqual(list(response.context["posts"]), [match])
        self.assertEqual(response.context["query"], "unicorn")

    def test_empty_query_shows_a_prompt_and_no_results(self):
        make_post()
        response = self.client.get(reverse("search-page"))
        self.assertEqual(list(response.context["posts"]), [])
        self.assertContains(response, "Type something above")

    def test_no_matches_shows_a_message(self):
        make_post()
        response = self.client.get(reverse("search-page"), {"q": "zzzznothing"})
        self.assertContains(response, "Nothing matched")

    def test_search_excludes_drafts(self):
        make_post("Unicorn draft", published=False)
        response = self.client.get(reverse("search-page"), {"q": "unicorn"})
        self.assertEqual(list(response.context["posts"]), [])

    def test_pagination_keeps_the_query_string(self):
        for i in range(3):
            make_post(f"Unicorn {i}")

        with self.settings(BLOG_SETTINGS=SETTINGS_TWO_PER_PAGE):
            response = self.client.get(reverse("search-page"), {"q": "unicorn"})

        self.assertContains(response, "q=unicorn")
        self.assertContains(response, "page=2")


class ReadLaterTests(TestCase):
    def setUp(self):
        self.post = make_post("Saveable")

    def test_empty_list_shows_a_prompt_and_a_way_onward(self):
        response = self.client.get(reverse("read-later"))

        self.assertFalse(response.context["has_posts"])
        self.assertContains(response, "Nothing saved yet")
        # A dead end otherwise: nothing to click and nowhere obvious to go.
        self.assertContains(response, "Browse all posts")

    def test_posting_adds_then_removes_the_post(self):
        url = reverse("read-later")

        self.client.post(url, {"post_id": self.post.id})
        self.assertEqual(self.client.session["stored_posts"], [self.post.id])

        self.client.post(url, {"post_id": self.post.id})
        self.assertEqual(self.client.session["stored_posts"], [])

    def test_saved_post_is_listed(self):
        self.client.post(reverse("read-later"), {"post_id": self.post.id})
        response = self.client.get(reverse("read-later"))
        self.assertTrue(response.context["has_posts"])
        self.assertContains(response, "Saveable")

    def test_detail_page_reflects_the_saved_state(self):
        first = self.client.get(self.post.get_absolute_url())
        self.assertFalse(first.context["saved_for_later"])

        self.client.post(reverse("read-later"), {"post_id": self.post.id})

        second = self.client.get(self.post.get_absolute_url())
        self.assertTrue(second.context["saved_for_later"])
        self.assertContains(second, "Remove from saved")

    def test_redirects_back_to_a_safe_next_target(self):
        response = self.client.post(
            reverse("read-later"),
            {"post_id": self.post.id, "next": self.post.get_absolute_url()},
        )
        self.assertRedirects(response, self.post.get_absolute_url())

    def test_refuses_an_offsite_next_target(self):
        response = self.client.post(
            reverse("read-later"),
            {"post_id": self.post.id, "next": "https://evil.example.com/steal"},
        )
        self.assertRedirects(response, reverse("read-later"))

    def test_malformed_post_id_is_handled(self):
        response = self.client.post(reverse("read-later"), {"post_id": "abc"})
        self.assertRedirects(response, reverse("read-later"))

        response = self.client.post(reverse("read-later"), {})
        self.assertRedirects(response, reverse("read-later"))

    def test_unpublished_saved_posts_are_not_listed(self):
        draft = make_post("Draft copy", published=False)
        session = self.client.session
        session["stored_posts"] = [draft.id]
        session.save()

        response = self.client.get(reverse("read-later"))

        self.assertFalse(response.context["has_posts"])


class ErrorPageTests(TestCase):
    """The custom error templates only render when DEBUG is off."""

    def test_404_page_renders_the_custom_template(self):
        with self.settings(DEBUG=False, ALLOWED_HOSTS=["testserver"]):
            response = self.client.get("/no-such-page")

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(response, "couldn't find that page", status_code=404)

    def test_500_and_403_templates_render(self):
        from django.template.loader import render_to_string

        self.assertIn("Something went wrong", render_to_string("500.html"))
        self.assertIn("Not allowed", render_to_string("403.html"))


class PageSizeTests(TestCase):
    """Six posts to a page, on every list that paginates."""

    def setUp(self):
        for i in range(8):
            make_post(f"Post {i}")

    def test_all_posts_shows_six_per_page(self):
        response = self.client.get(reverse("posts-page"))

        self.assertEqual(len(response.context["posts"]), 6)
        self.assertEqual(response.context["paginator"].num_pages, 2)

    def test_second_page_holds_the_remainder(self):
        response = self.client.get(reverse("posts-page"), {"page": 2})
        self.assertEqual(len(response.context["posts"]), 2)

    def test_tag_and_author_pages_use_the_same_size(self):
        tag = make_tag("Japan")
        author = make_author("Ada", "Lovelace")
        for i in range(7):
            make_post(f"Tagged {i}", author=author, tags=[tag])

        for url in (tag.get_absolute_url(), author.get_absolute_url()):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(len(response.context["posts"]), 6)

    def test_search_uses_the_same_size(self):
        for i in range(7):
            make_post(f"Unicorn {i}")

        response = self.client.get(reverse("search-page"), {"q": "unicorn"})

        self.assertEqual(len(response.context["posts"]), 6)


class TemplateCommentLeakTests(TestCase):
    """Django's ``{# #}`` is single-line only.

    Spread over two lines it stops being a comment: the opening text renders
    as visible page content and the rest of the tag swallows the markup after
    it. That failure still passes ordinary ``assertContains`` checks, because
    the words are all technically present — so it needs its own test.
    """

    def setUp(self):
        self.post = make_post("Leak Check", tags=[make_tag("Oita")])
        make_comment(self.post)

    def test_no_page_renders_a_raw_template_comment(self):
        paths = [
            "/",
            "/posts",
            self.post.get_absolute_url(),
            "/tags/oita",
            "/search?q=leak",
            "/read-later",
            "/credits",
        ]
        for path in paths:
            with self.subTest(path=path):
                body = self.client.get(path).content.decode()
                self.assertNotIn("{#", body)
                self.assertNotIn("#}", body)
                self.assertNotIn("{%", body)


class HeroPostCountTests(TestCase):
    """The hero's "N posts so far" is counted per request, never stored."""

    def test_it_counts_the_whole_archive_not_the_cards_shown(self):
        # The home page shows a handful of cards; the count is the full total.
        for i in range(9):
            make_post(f"Post {i}", slug=f"post-{i}")

        response = self.client.get("/")

        self.assertEqual(response.context["total_posts"], 9)
        self.assertContains(response, "9")

    def test_it_goes_up_when_a_post_is_added(self):
        make_post("First", slug="first")
        self.assertEqual(self.client.get("/").context["total_posts"], 1)

        make_post("Second", slug="second")
        self.assertEqual(self.client.get("/").context["total_posts"], 2)

    def test_it_goes_down_when_a_post_is_deleted(self):
        first = make_post("First", slug="first")
        make_post("Second", slug="second")
        self.assertEqual(self.client.get("/").context["total_posts"], 2)

        first.delete()
        self.assertEqual(self.client.get("/").context["total_posts"], 1)

    def test_drafts_and_future_posts_are_not_counted(self):
        make_post("Live", slug="live")
        make_post("Hidden", slug="hidden", published=False)
        make_future_post("Later", slug="later")

        self.assertEqual(self.client.get("/").context["total_posts"], 1)

    def test_the_wording_agrees_with_the_number(self):
        make_post("Only One", slug="only-one")
        self.assertContains(self.client.get("/"), "post so far")

        make_post("And Another", slug="and-another")
        self.assertContains(self.client.get("/"), "posts so far")

    def test_an_empty_blog_shows_no_count_at_all(self):
        self.assertNotContains(self.client.get("/"), "posts so far")


class PostCardTests(TestCase):
    """The card is one link; the cue inside it must not be a second one."""

    def setUp(self):
        self.post = make_post("Clickable", slug="clickable")

    def test_every_card_shows_a_read_more_cue(self):
        for url in ("/", "/posts"):
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), "Read more")

    def test_the_cue_is_not_a_nested_link(self):
        # <a> inside <a> is invalid and browsers handle it unpredictably.
        body = self.client.get("/").content.decode()
        card = body[body.index('class="post"') : body.index("</article>")]

        self.assertIn('class="post__more"', card)
        self.assertEqual(card.count("<a "), 1)

    def test_the_whole_card_is_still_the_link(self):
        body = self.client.get("/").content.decode()
        card = body[body.index('class="post"') : body.index("</article>")]

        self.assertIn(self.post.get_absolute_url(), card)
        # Picture and text both sit inside the single anchor.
        anchor = card[card.index("<a ") :]
        self.assertIn("post__content", anchor)

    def test_the_arrow_is_hidden_from_screen_readers(self):
        # "Read more →" should be announced as "Read more", not "Read more
        # right arrow".
        self.assertContains(self.client.get("/"), '<span aria-hidden="true">')


class StickyFooterTests(TestCase):
    """A short page must not leave the footer floating mid-window."""

    def _css(self):
        with open(Path(settings.BASE_DIR) / "static" / "app.css") as handle:
            return handle.read()

    def test_content_sits_in_a_growing_wrapper(self):
        for url in ("/", "/read-later", "/posts"):
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), '<div class="page">')

    def test_the_body_is_a_full_height_column(self):
        css = self._css()
        rule = css[css.index("body {") :].split("}")[0]

        self.assertIn("flex-direction: column", rule)
        self.assertIn("min-height: 100dvh", rule)

    def test_the_wrapper_grows_to_fill_the_window(self):
        css = self._css()
        rule = css[css.index(".page {") :].split("}")[0]
        self.assertIn("flex: 1 0 auto", rule)

    def test_the_home_page_is_flagged_for_its_white_footer(self):
        # A body class, not an adjacent-sibling selector: the content wrapper
        # now sits between #about and the footer.
        self.assertContains(self.client.get("/"), 'class="has-about"')
        self.assertNotContains(self.client.get("/posts"), 'class="has-about"')

    def test_the_read_more_cue_is_pinned_to_the_bottom_of_the_card(self):
        # Without margin-top:auto it floats up under short excerpts, so it
        # lands on a different line in every card of a row.
        with open(
            Path(settings.BASE_DIR) / "blog" / "static" / "blog" / "post.css"
        ) as f:
            css = f.read()
        rule = css[css.index(".post__more {") :].split("}")[0]
        self.assertIn("margin-top: auto", rule)

    def test_card_grids_give_every_row_the_same_height(self):
        # Otherwise row two can be taller than row one and the cue sits on a
        # different line down the page.
        base = Path(settings.BASE_DIR) / "blog" / "static" / "blog"
        for name, selector in (
            ("index.css", "#latest-posts ul {"),
            ("all-posts.css", "#all-posts ul {"),
        ):
            with self.subTest(stylesheet=name):
                with open(base / name) as handle:
                    css = handle.read()
                rule = css[css.index(selector) :].split("}")[0]
                self.assertIn("grid-auto-rows: 1fr", rule)


# Uploads in this test go to a throwaway directory, never the real uploads/.
SAVED_MEDIA_ROOT = tempfile.mkdtemp(prefix="blog-saved-test-")


@override_settings(MEDIA_ROOT=SAVED_MEDIA_ROOT)
class SavedPageTests(TestCase):
    """The reading list: enough on each row to choose from, and safe markup."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(SAVED_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.post = make_post(
            "A Saved Post", slug="a-saved-post", image=make_image_file("saved.jpg")
        )
        self.client.post(reverse("read-later"), {"post_id": self.post.id})

    def test_each_row_shows_the_picture_title_date_and_length(self):
        response = self.client.get(reverse("read-later"))

        self.assertContains(response, "saved-item__thumb")
        self.assertContains(response, "A Saved Post")
        self.assertContains(response, self.post.published_at.strftime("%d %b %Y"))
        self.assertContains(response, "min read")

    def test_the_count_agrees_with_the_list(self):
        response = self.client.get(reverse("read-later"))
        self.assertContains(response, "1 post waiting")

        second = make_post("Another", slug="another")
        self.client.post(reverse("read-later"), {"post_id": second.id})
        self.assertContains(self.client.get(reverse("read-later")), "2 posts waiting")

    def test_the_remove_button_is_not_nested_inside_the_link(self):
        # A <button> inside an <a> is invalid, and clicking it would follow the
        # link instead of removing the post.
        body = self.client.get(reverse("read-later")).content.decode()
        # Search for the closing tag from the row's own position: other <li>
        # elements on the page would otherwise end the slice early.
        start = body.index('class="saved-item"')
        row = body[start : body.index("</li>", start)]

        link = row[row.index("<a ") : row.index("</a>")]
        self.assertNotIn("<button", link)
        self.assertNotIn("<form", link)

    def test_the_remove_button_says_what_it_removes(self):
        # The visible control is just "×", which tells a screen reader nothing.
        response = self.client.get(reverse("read-later"))
        self.assertContains(response, "Remove “A Saved Post” from saved")

    def test_removing_from_the_list_works_and_returns_here(self):
        response = self.client.post(
            reverse("read-later"),
            {"post_id": self.post.id, "next": reverse("read-later")},
            follow=True,
        )

        self.assertContains(response, "Nothing saved yet")
        self.assertNotContains(response, "saved-item__thumb")

    def test_a_post_without_a_picture_still_lines_up(self):
        plain = make_post("No Picture", slug="no-picture")
        self.client.post(reverse("read-later"), {"post_id": plain.id})

        response = self.client.get(reverse("read-later"))
        self.assertContains(response, "saved-item__thumb--empty")


class TestIsolationTests(TestCase):
    """Running the suite must not leave anything behind in the real project."""

    def test_no_test_writes_into_the_real_uploads_directory(self):
        # A test that saves an ImageField without overriding MEDIA_ROOT writes
        # a file into uploads/ on every run, which then shows up in git status.
        import re

        suite_dir = Path(settings.BASE_DIR) / "blog" / "tests"
        for path in sorted(suite_dir.glob("test_*.py")):
            source = path.read_text()
            with self.subTest(module=path.name):
                if (
                    "make_image_file" not in source
                    and "make_gallery_image" not in source
                ):
                    continue
                self.assertTrue(
                    re.search(r"MEDIA_ROOT\s*=", source),
                    f"{path.name} creates image uploads but never overrides "
                    "MEDIA_ROOT, so it writes into the real uploads/ folder",
                )


PERF_MEDIA_ROOT = tempfile.mkdtemp(prefix="blog-perf-test-")


@override_settings(MEDIA_ROOT=PERF_MEDIA_ROOT)
class ResponsiveImageTests(TestCase):
    """Cards ask for a card-sized file, not the full-size original."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(PERF_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.post = make_post(
            "Wide", slug="wide", image=make_image_file("wide.jpg", size=(1600, 1067))
        )

    def test_cards_offer_a_smaller_variant(self):
        response = self.client.get("/")

        self.assertContains(response, "srcset=")
        self.assertContains(response, "800w")
        self.assertContains(response, "sizes=")

    def test_the_thumbnail_is_actually_smaller_than_the_original(self):
        from blog.imaging import build_thumbnail

        thumb = build_thumbnail(self.post.image.storage, self.post.image.name)
        original = self.post.image.storage.size(self.post.image.name)
        reduced = self.post.image.storage.size(thumb)

        self.assertLess(reduced, original)

    def test_src_still_names_the_full_image(self):
        # A browser that ignores srcset must still get a working picture.
        response = self.client.get("/")
        self.assertContains(response, self.post.image.url)

    def test_an_already_small_image_gets_no_pointless_variant(self):
        small = make_post(
            "Small", slug="small", image=make_image_file("small.jpg", size=(300, 200))
        )
        from blog.imaging import build_thumbnail

        self.assertIsNone(build_thumbnail(small.image.storage, small.image.name))

    def test_a_missing_file_does_not_break_the_page(self):
        self.post.image.storage.delete(self.post.image.name)
        self.assertEqual(self.client.get("/").status_code, 200)

    @staticmethod
    def _candidates(body):
        """The srcset widths on the page, ascending."""
        import re

        entry = re.search(r'srcset="([^"]+)"', body).group(1)
        return sorted(int(w) for w in re.findall(r"\s(\d+)w", entry))

    def test_a_phone_at_3x_is_not_sent_the_full_size_original(self):
        # The bug this guards. Cards are sized 92vw on a phone, so a 393px
        # handset at 3x asks for ~1085 device px. A browser takes the smallest
        # candidate that still covers that; with only 800w and the 1600w
        # original in the list, 800 does not cover it and it downloads the
        # original — the single heaviest thing on the page, three times over.
        widths = self._candidates(self.client.get("/").content.decode())
        needed = round(393 * 0.92 * 3)

        chosen = min((w for w in widths if w >= needed), default=max(widths))

        self.assertLess(
            chosen,
            1600,
            f"a phone needing {needed}px is served the {chosen}px original; "
            f"candidates were {widths}",
        )

    def test_variants_are_offered_smallest_first(self):
        import re

        body = self.client.get("/").content.decode()
        entries = re.search(r'srcset="([^"]+)"', body).group(1).split(",")
        widths = [int(e.strip().split(" ")[1].rstrip("w")) for e in entries]

        self.assertEqual(widths, sorted(widths))

    def test_dimensions_are_still_emitted_so_layout_does_not_shift(self):
        # Losing width/height while adding srcset would trade page weight for
        # layout shift, which Google measures.
        response = self.client.get("/")
        self.assertContains(response, 'width="1600"')
        self.assertContains(response, 'height="1067"')


class FontLoadingTests(TestCase):
    def test_fonts_are_linked_from_the_head_not_imported_from_css(self):
        # An @import cannot start downloading until app.css has arrived and
        # been parsed — two serial round trips before any text can paint.
        import re

        with open(Path(settings.BASE_DIR) / "static" / "app.css") as handle:
            css = handle.read()
        # Comments stripped first: the note explaining why there is no @import
        # here naturally contains the word.
        code = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        self.assertNotIn("@import", code)

        response = self.client.get("/")
        self.assertContains(response, "fonts.googleapis.com/css2")
        self.assertContains(response, 'rel="preconnect"')
