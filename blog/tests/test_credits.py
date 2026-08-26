"""Tests for the photo credits page and the file that feeds it."""

import json
import tempfile
from pathlib import Path
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from blog import credits

CREDIT_ROWS = {
    "posts/beppu.jpg": {
        "post": "The Steaming Streets of Beppu",
        "post_url": "/posts/the-steaming-streets-of-beppu",
        "artist": "663highland",
        "licence": "CC BY 2.5",
        "licence_url": "https://creativecommons.org/licenses/by/2.5",
        "source": "https://commons.wikimedia.org/wiki/File:Beppu.jpg",
    },
    "gallery/beppu-city.jpg": {
        "post": "The Steaming Streets of Beppu",
        "post_url": "/posts/the-steaming-streets-of-beppu",
        "artist": "Somebody Else",
        "licence": "CC0",
        "licence_url": "",
        "source": "https://commons.wikimedia.org/wiki/File:Beppu_City.jpg",
    },
    "posts/yufuin.jpg": {
        "post": "A Slow Morning in Yufuin",
        "post_url": "/posts/a-slow-morning-in-yufuin",
        "artist": "A Third Person",
        "licence": "CC BY-SA 4.0",
        "licence_url": "https://creativecommons.org/licenses/by-sa/4.0",
        "source": "https://commons.wikimedia.org/wiki/File:Yufuin.jpg",
    },
}


class _CreditsFile:
    """Point blog.credits at a temporary file for the duration of a test."""

    def __init__(self, rows):
        self.rows = rows

    def __enter__(self):
        self._dir = tempfile.TemporaryDirectory()
        path = Path(self._dir.name) / "photo_credits.json"
        if self.rows is not None:
            path.write_text(json.dumps(self.rows))
        self._patch = mock.patch.object(credits, "ATTRIBUTIONS_PATH", path)
        self._patch.start()
        return path

    def __exit__(self, *exc):
        self._patch.stop()
        self._dir.cleanup()


class CreditsLoadingTests(TestCase):
    def test_missing_file_means_no_credits(self):
        with _CreditsFile(None):
            self.assertEqual(credits.load(), [])
            self.assertEqual(credits.grouped(), [])

    def test_rows_carry_their_filename(self):
        with _CreditsFile(CREDIT_ROWS):
            files = {row["file"] for row in credits.load()}
        self.assertEqual(files, set(CREDIT_ROWS))

    def test_photos_are_grouped_under_their_post(self):
        with _CreditsFile(CREDIT_ROWS):
            groups = credits.grouped()

        self.assertEqual(len(groups), 2)
        by_title = {group["title"]: group for group in groups}
        self.assertEqual(len(by_title["The Steaming Streets of Beppu"]["photos"]), 2)
        self.assertEqual(len(by_title["A Slow Morning in Yufuin"]["photos"]), 1)


class CreditsPageTests(TestCase):
    def test_the_page_lists_photographers_and_licences(self):
        with _CreditsFile(CREDIT_ROWS):
            response = self.client.get(reverse("photo-credits"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "663highland")
        self.assertContains(response, "CC BY 2.5")
        self.assertContains(response, "The Steaming Streets of Beppu")
        self.assertContains(response, "commons.wikimedia.org")

    def test_a_licence_without_a_url_still_shows_its_name(self):
        with _CreditsFile(CREDIT_ROWS):
            response = self.client.get(reverse("photo-credits"))
        self.assertContains(response, "CC0")

    def test_the_page_is_kept_out_of_search_results(self):
        # Useful to a reader and required by the licences, but not content
        # worth indexing.
        with _CreditsFile(CREDIT_ROWS):
            response = self.client.get(reverse("photo-credits"))
        self.assertContains(response, "noindex")

    def test_the_page_survives_having_nothing_to_credit(self):
        with _CreditsFile(None):
            response = self.client.get(reverse("photo-credits"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Every picture on this blog is my own.")


class CreditsFileSafetyTests(TestCase):
    def test_the_command_resolves_the_path_at_call_time(self):
        """Guards against re-binding the path at import.

        ``from blog.credits import ATTRIBUTIONS_PATH`` would make the constant
        unpatchable, and running the suite would then overwrite the real
        blog/photo_credits.json with test fixtures.
        """
        from blog.management.commands import seed_kyushu

        self.assertFalse(
            hasattr(seed_kyushu, "ATTRIBUTIONS_PATH"),
            "seed_kyushu must reach the path through the credits module",
        )


class CreditsPagePlacementTests(TestCase):
    def test_the_footer_does_not_link_the_credits_page(self):
        # Deliberately unlinked: see the note in blog/credits.py.
        with _CreditsFile(CREDIT_ROWS):
            body = self.client.get("/").content.decode()

        footer = body[body.index("site-footer") :]
        self.assertNotIn(reverse("photo-credits"), footer)

    def test_the_page_is_still_reachable_directly(self):
        with _CreditsFile(CREDIT_ROWS):
            response = self.client.get(reverse("photo-credits"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "663highland")

    def test_crawlers_are_told_to_skip_it(self):
        response = self.client.get("/robots.txt")
        self.assertContains(response, "Disallow: /credits")
