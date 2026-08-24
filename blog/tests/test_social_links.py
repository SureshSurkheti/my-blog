"""Social profile links: built from the environment, rendered site-wide."""

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
    def test_links_appear_in_the_footer_on_every_page(self):
        post = make_post("Anywhere")
        for url in (
            reverse("starting-page"),
            reverse("posts-page"),
            post.get_absolute_url(),
            reverse("read-later"),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "https://github.com/example")

    @override_settings(SOCIAL_LINKS=LINKS)
    def test_links_open_safely_and_claim_identity(self):
        response = self.client.get(reverse("starting-page"))
        self.assertContains(response, 'rel="me noopener"')
        self.assertContains(response, 'target="_blank"')

    @override_settings(SOCIAL_LINKS=LINKS)
    def test_they_appear_once_per_page_in_the_footer_only(self):
        body = self.client.get(reverse("starting-page")).content.decode()

        self.assertEqual(body.count('class="social-links'), 1)
        # Not repeated inside the homepage bio panel.
        bio = body[body.index('id="about"') : body.index("site-footer")]
        self.assertNotIn("social-link", bio)

    @override_settings(SOCIAL_LINKS=[])
    def test_nothing_renders_when_none_are_configured(self):
        response = self.client.get(reverse("starting-page"))
        self.assertNotContains(response, "social-link")

    @override_settings(SOCIAL_LINKS=LINKS)
    def test_labels_are_the_link_text_so_no_aria_label_is_needed(self):
        response = self.client.get(reverse("starting-page"))
        self.assertContains(response, "GitHub")
        self.assertContains(response, "Instagram")
