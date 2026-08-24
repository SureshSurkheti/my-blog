from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from blog.models import Comment

from .factories import make_author, make_comment, make_future_post, make_post, make_tag

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

    def test_empty_list_shows_a_prompt(self):
        response = self.client.get(reverse("read-later"))
        self.assertFalse(response.context["has_posts"])
        self.assertContains(response, "haven't saved any posts")

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
