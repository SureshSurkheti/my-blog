"""Social profile links: built from the environment, rendered site-wide."""

import re

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from my_site.social import build_social_links

from .factories import make_post

LINKS = [
    {"key": "github", "label": "GitHub", "url": "https://github.com/example"},
    {
        "key": "instagram",
        "label": "Instagram",
        "url": "https://www.instagram.com/example",
    },
]


def fake_env(values):
    """Stand-in for django-environ's callable, which takes a default kwarg."""

    def env(name, default=""):
        return values.get(name, default)

    return env


class BuildSocialLinksTests(SimpleTestCase):
    def test_bare_handle_is_expanded(self):
        links = build_social_links(fake_env({"SOCIAL_GITHUB": "someone"}))
        self.assertEqual(
            links,
            [{"key": "github", "label": "GitHub", "url": "https://github.com/someone"}],
        )

    def test_leading_at_sign_is_dropped(self):
        links = build_social_links(fake_env({"SOCIAL_X": "@someone"}))
        self.assertEqual(links[0]["url"], "https://x.com/someone")

    def test_full_url_is_used_as_given(self):
        links = build_social_links(
            fake_env({"SOCIAL_INSTAGRAM": "https://instagr.am/other"})
        )
        self.assertEqual(links[0]["url"], "https://instagr.am/other")

    def test_blank_and_whitespace_entries_are_skipped(self):
        self.assertEqual(build_social_links(fake_env({})), [])
        self.assertEqual(build_social_links(fake_env({"SOCIAL_GITHUB": "   "})), [])

    def test_platforms_without_a_pattern_need_a_full_url(self):
        # A bare handle can't be expanded for Mastodon, so it is ignored...
        self.assertEqual(build_social_links(fake_env({"SOCIAL_MASTODON": "me"})), [])
        # ...but a full URL works.
        links = build_social_links(
            fake_env({"SOCIAL_MASTODON": "https://mastodon.social/@me"})
        )
        self.assertEqual(links[0]["url"], "https://mastodon.social/@me")

    def test_order_follows_the_platform_list(self):
        links = build_social_links(
            fake_env({"SOCIAL_GITHUB": "a", "SOCIAL_INSTAGRAM": "b"})
        )
        self.assertEqual([link["key"] for link in links], ["instagram", "github"])

    def test_facebook_and_tiktok_are_supported(self):
        links = build_social_links(
            fake_env({"SOCIAL_FACEBOOK": "me", "SOCIAL_TIKTOK": "@me"})
        )
        self.assertEqual(
            [(link["key"], link["url"]) for link in links],
            [
                ("facebook", "https://www.facebook.com/me"),
                ("tiktok", "https://www.tiktok.com/@me"),
            ],
        )


class SocialLinkRenderingTests(TestCase):
    @override_settings(SOCIAL_LINKS=LINKS)
    def test_links_appear_in_the_footer_of_every_page(self):
        # The whole point of the footer over the home hero: a reader who lands
        # on a post from a search engine can still find them.
        post = make_post("Anywhere")
        for url in (
            reverse("starting-page"),
            reverse("posts-page"),
            post.get_absolute_url(),
            reverse("read-later"),
            reverse("search-page"),
        ):
            with self.subTest(url=url):
                body = self.client.get(url).content.decode()
                footer = body[body.index("site-footer") :]
                self.assertIn("https://github.com/example", footer)

    @override_settings(SOCIAL_LINKS=LINKS)
    def test_links_are_not_in_the_header(self):
        # A follow button in the nav is a way off the site offered before any
        # of the writing has been read.
        body = self.client.get(reverse("starting-page")).content.decode()

        header = body[body.index('id="main-navigation"') : body.index("</header>")]
        self.assertNotIn("social-link", header)

    @override_settings(SOCIAL_LINKS=LINKS)
    def test_links_are_not_duplicated_in_the_home_hero(self):
        body = self.client.get(reverse("starting-page")).content.decode()

        hero = body[body.index('id="welcome"') : body.index('id="latest-posts"')]
        self.assertNotIn("social-link", hero)

    @override_settings(SOCIAL_LINKS=LINKS)
    def test_links_open_safely_and_claim_identity(self):
        response = self.client.get(reverse("starting-page"))
        self.assertContains(response, 'rel="me noopener"')
        self.assertContains(response, 'target="_blank"')

    @override_settings(SOCIAL_LINKS=LINKS)
    def test_they_render_once_per_page(self):
        body = self.client.get(reverse("starting-page")).content.decode()
        self.assertEqual(body.count('class="social-links'), 1)

    @override_settings(SOCIAL_LINKS=[])
    def test_nothing_renders_when_none_are_configured(self):
        response = self.client.get(reverse("starting-page"))
        self.assertNotContains(response, "social-link")

    @override_settings(SOCIAL_LINKS=LINKS)
    def test_every_platform_name_is_still_readable(self):
        response = self.client.get(reverse("starting-page"))
        self.assertContains(response, "GitHub")
        self.assertContains(response, "Instagram")


class SocialIconTests(TestCase):
    """Every configured platform must render a glyph, and stay reachable."""

    @override_settings(
        SOCIAL_LINKS=[
            {"key": "instagram", "label": "Instagram", "url": "https://i.test/me"},
            {"key": "linkedin", "label": "LinkedIn", "url": "https://l.test/me"},
        ]
    )
    def test_each_link_renders_an_icon(self):
        response = self.client.get("/")
        body = response.content.decode()

        self.assertEqual(body.count('class="social-link__icon"'), 2)
        self.assertEqual(body.count("<svg"), body.count("</svg>"))

    @override_settings(
        SOCIAL_LINKS=[
            {"key": "instagram", "label": "Instagram", "url": "https://i.test/me"},
        ]
    )
    def test_the_name_survives_for_people_who_cannot_see_the_glyph(self):
        # An icon-only link is unreadable to a screen reader without this.
        response = self.client.get("/")

        self.assertContains(response, 'title="Instagram"')
        self.assertContains(response, '<span class="visually-hidden">Instagram</span>')

    @override_settings(
        SOCIAL_LINKS=[
            {"key": "instagram", "label": "Instagram", "url": "https://i.test/me"},
        ]
    )
    def test_the_follow_heading_appears_with_the_links(self):
        self.assertContains(self.client.get("/"), "Follow me")

    @override_settings(SOCIAL_LINKS=[])
    def test_no_heading_when_nothing_is_configured(self):
        response = self.client.get("/")

        self.assertNotContains(response, "Follow me")
        self.assertNotContains(response, "social-link")

    @override_settings(
        SOCIAL_LINKS=[
            {"key": "brand-new", "label": "Brand New", "url": "https://n.test/me"},
        ]
    )
    def test_a_platform_with_no_glyph_still_renders_something(self):
        # Otherwise adding a SOCIAL_* handle for a new platform would show an
        # empty circle with no way to tell what it links to.
        response = self.client.get("/")

        self.assertContains(response, 'class="social-link__icon"')
        self.assertContains(response, 'title="Brand New"')


class AuthorSiteTests(TestCase):
    """The link to the author's own site in the About section."""

    @override_settings(
        AUTHOR_SITE={"name": "Suresh Surkheti", "url": "https://sureshsurkheti.com"}
    )
    def test_the_about_section_links_to_the_authors_own_site(self):
        response = self.client.get(reverse("starting-page"))

        self.assertContains(response, 'href="https://sureshsurkheti.com"')
        # Shown without the scheme: it reads as a name, not a URL.
        self.assertContains(response, ">sureshsurkheti.com<")

    @override_settings(
        AUTHOR_SITE={"name": "Suresh Surkheti", "url": "https://sureshsurkheti.com"}
    )
    def test_the_link_claims_the_site_as_the_same_person(self):
        # rel="me" is what lets the two sites verify each other. Matched as a
        # token, not as the whole attribute: rel carries noopener alongside it.
        response = self.client.get(reverse("starting-page"))
        link = re.search(
            r'<a href="https://sureshsurkheti\.com"[^>]*>', response.content.decode()
        ).group(0)
        rel = re.search(r'rel="([^"]*)"', link).group(1)

        self.assertIn("me", rel.split())

    @override_settings(
        AUTHOR_SITE={"name": "Suresh Surkheti", "url": "https://sureshsurkheti.com"}
    )
    def test_the_link_opens_in_a_new_tab_without_handing_over_the_opener(self):
        # target="_blank" alone lets the opened page reach back through
        # window.opener, so the two must be asserted together.
        response = self.client.get(reverse("starting-page"))
        link = re.search(
            r'<a href="https://sureshsurkheti\.com"[^>]*>', response.content.decode()
        ).group(0)

        self.assertIn('target="_blank"', link)
        self.assertIn("noopener", link)

    @override_settings(
        AUTHOR_SITE={"name": "Suresh Surkheti", "url": "https://sureshsurkheti.com"}
    )
    def test_a_screen_reader_is_told_the_tab_will_change(self):
        response = self.client.get(reverse("starting-page"))

        self.assertContains(response, "(opens in a new tab)")

    @override_settings(AUTHOR_SITE={"name": "Suresh Surkheti", "url": ""})
    def test_nothing_renders_when_no_site_is_configured(self):
        response = self.client.get(reverse("starting-page"))

        self.assertNotContains(response, "about__site")

    @override_settings(
        AUTHOR_SITE={"name": "Suresh Surkheti", "url": "https://sureshsurkheti.com"}
    )
    def test_the_link_is_only_on_the_home_page(self):
        # It is the one outbound link on the site; repeating it on every page
        # would make it noise rather than an invitation.
        response = self.client.get(reverse("posts-page"))

        self.assertNotContains(response, "about__site")
