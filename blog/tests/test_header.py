"""The site header: active-section marking and the collapsible search."""

from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from .factories import make_author, make_post, make_tag


class ActiveSectionTests(TestCase):
    def setUp(self):
        self.tag = make_tag("Japan")
        self.author = make_author("Ada", "Lovelace")
        self.post = make_post("A post", author=self.author, tags=[self.tag])

    def test_all_posts_is_marked_across_the_archive(self):
        for url in (
            reverse("posts-page"),
            self.post.get_absolute_url(),
            self.tag.get_absolute_url(),
            self.author.get_absolute_url(),
            reverse("search-page"),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'aria-current="page"')
                self.assertContains(response, 'class="is-active"')

    def test_read_later_marks_its_own_link(self):
        response = self.client.get(reverse("read-later"))
        body = response.content.decode()
        # Search inside <nav> only: the URL also appears in <head> as the
        # canonical link, which would otherwise match first.
        nav = body[body.index("<nav") : body.index("</nav>")]
        # The marker sits on the Saved link, not the archive one.
        stored_index = nav.index(reverse("read-later"))
        self.assertIn('aria-current="page"', nav[stored_index : stored_index + 200])

    def test_homepage_marks_nothing(self):
        response = self.client.get(reverse("starting-page"))
        self.assertNotContains(response, 'aria-current="page"')

    def test_only_one_link_is_ever_marked(self):
        response = self.client.get(reverse("posts-page"))
        self.assertEqual(response.content.decode().count('aria-current="page"'), 1)


class HeaderSearchTests(TestCase):
    def test_search_form_is_present_and_usable_without_javascript(self):
        response = self.client.get(reverse("starting-page"))

        # The form ships visible; only the script collapses it.
        self.assertContains(response, 'id="nav-search-form"')
        self.assertContains(response, 'action="/search"')
        self.assertContains(response, 'name="q"')

    def test_toggle_button_starts_hidden_for_scriptless_visitors(self):
        response = self.client.get(reverse("starting-page"))
        self.assertContains(response, "data-nav-search-toggle")
        self.assertContains(response, 'aria-expanded="false"')
        self.assertContains(response, "hidden")

    def test_toggle_is_labelled_and_wired_to_the_form(self):
        response = self.client.get(reverse("starting-page"))
        self.assertContains(response, 'aria-controls="nav-search-form"')
        self.assertContains(response, 'aria-label="Search posts"')

    def test_script_is_loaded_on_every_page(self):
        post = make_post("Anywhere")
        for url in (
            reverse("starting-page"),
            reverse("posts-page"),
            post.get_absolute_url(),
        ):
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), "nav.js")

    def test_the_search_term_is_kept_in_the_field(self):
        response = self.client.get(reverse("search-page"), {"q": "beppu"})
        self.assertContains(response, 'value="beppu"')


class HeaderMarkupTests(TestCase):
    def test_title_links_home_and_both_label_lengths_are_present(self):
        response = self.client.get(reverse("posts-page"))

        self.assertContains(response, 'class="site-title"')
        # Full labels for wide screens, short ones for phones.
        self.assertContains(response, "All Posts")
        self.assertContains(response, "Posts</span>")
        self.assertContains(response, "Saved")

    def test_nav_is_labelled_for_assistive_tech(self):
        response = self.client.get(reverse("posts-page"))
        self.assertContains(response, '<nav aria-label="Main">')


class ConsistentNamingTests(TestCase):
    """One name for the reading list, everywhere it is mentioned."""

    def test_nav_calls_it_saved(self):
        response = self.client.get(reverse("starting-page"))
        self.assertContains(response, "Saved")
        self.assertNotContains(response, "Stored Posts")

    def test_the_list_page_calls_it_saved(self):
        response = self.client.get(reverse("read-later"))
        self.assertContains(response, "<h1>Saved</h1>", html=True)
        self.assertNotContains(response, "Read Later")
        # One label, not a longer variant on the page it belongs to.
        self.assertNotContains(response, "Saved posts")

    def test_the_post_button_uses_the_same_word(self):
        post = make_post("Saveable")

        unsaved = self.client.get(post.get_absolute_url())
        self.assertContains(unsaved, "Save for later")
        self.assertNotContains(unsaved, "Read Later")

        self.client.post(reverse("read-later"), {"post_id": post.id})

        saved = self.client.get(post.get_absolute_url())
        self.assertContains(saved, "Remove from saved")

    def test_the_confirmation_message_uses_the_same_word(self):
        post = make_post("Saveable")
        response = self.client.post(
            reverse("read-later"), {"post_id": post.id}, follow=True
        )
        self.assertContains(response, "Saved for later")

    def test_the_title_is_not_underlined_on_hover(self):
        # The rule lives in the stylesheet, so assert on what ships.
        with open("static/app.css") as handle:
            css = handle.read()
        title_block = css[css.index(".site-title {") : css.index(".site-title:focus")]
        self.assertNotIn("text-decoration: underline", title_block)


class VisuallyHiddenTests(TestCase):
    """Screen-reader-only labels must actually be hidden on screen.

    This class went missing from the stylesheet during an unrelated edit and
    the "Search posts" label rendered as visible black text in the header —
    nothing failed, so it went unnoticed. These assertions make that loud.
    """

    def _stylesheet(self):
        with open(Path(settings.BASE_DIR) / "static" / "app.css") as handle:
            return handle.read()

    def test_the_utility_class_is_defined(self):
        css = self._stylesheet()

        self.assertIn(".visually-hidden {", css)
        rule = css[css.index(".visually-hidden {") :].split("}")[0]
        # The clip pattern: off-screen but still announced.
        self.assertIn("position: absolute", rule)
        self.assertIn("clip-path", rule)
        self.assertIn("width: 1px", rule)

    def test_every_use_of_the_class_has_a_definition(self):
        css = self._stylesheet()
        for template in ("templates/base.html", "blog/templates/blog/search.html"):
            with self.subTest(template=template):
                with open(Path(settings.BASE_DIR) / template) as handle:
                    markup = handle.read()
                if "visually-hidden" in markup:
                    self.assertIn(".visually-hidden {", css)

    def test_the_search_label_is_present_for_assistive_tech(self):
        response = self.client.get(reverse("posts-page"))
        self.assertContains(response, 'class="visually-hidden" for="nav-search-input"')
