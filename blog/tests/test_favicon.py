"""Site icons: present in the markup, served, and valid image files."""

import json
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from PIL import Image

STATIC = Path(settings.BASE_DIR) / "static"

EXPECTED = {
    "favicon-32.png": 32,
    "apple-touch-icon.png": 180,
    "icon-192.png": 192,
    "icon-512.png": 512,
}


class IconFileTests(TestCase):
    def test_every_png_exists_at_its_declared_size(self):
        for name, size in EXPECTED.items():
            with self.subTest(name=name):
                path = STATIC / name
                self.assertTrue(path.exists(), f"{name} is missing")
                with Image.open(path) as image:
                    self.assertEqual(image.size, (size, size))

    def test_ico_carries_several_resolutions(self):
        with Image.open(STATIC / "favicon.ico") as image:
            self.assertGreaterEqual(len(image.ico.sizes()), 3)

    def test_apple_touch_icon_has_no_transparency(self):
        """iOS ignores alpha and composites onto black, ringing a rounded icon."""
        with Image.open(STATIC / "apple-touch-icon.png") as image:
            self.assertNotIn("A", image.getbands())

    def test_manifest_is_valid_json_and_points_at_real_files(self):
        manifest = json.loads((STATIC / "site.webmanifest").read_text())

        self.assertEqual(manifest["name"], "Suresh's Blog")
        for icon in manifest["icons"]:
            name = icon["src"].rsplit("/", 1)[-1]
            with self.subTest(icon=name):
                self.assertTrue((STATIC / name).exists())

    def test_the_theme_colour_matches_the_icon(self):
        manifest = json.loads((STATIC / "site.webmanifest").read_text())
        with open(Path(settings.BASE_DIR) / "templates" / "base.html") as handle:
            markup = handle.read()

        # One colour, taken from the icon, in both places.
        self.assertIn(manifest["theme_color"], markup)


class IconMarkupTests(TestCase):
    def test_head_declares_the_icons(self):
        response = self.client.get(reverse("starting-page"))

        self.assertContains(response, 'rel="icon"')
        self.assertContains(response, "favicon.ico")
        self.assertContains(response, "favicon-32.png")
        self.assertContains(response, 'rel="apple-touch-icon"')
        self.assertContains(response, 'rel="manifest"')
        self.assertContains(response, 'name="theme-color"')

    def test_icons_are_declared_on_every_page(self):
        from .factories import make_post

        post = make_post("Anywhere")
        for url in (
            reverse("posts-page"),
            post.get_absolute_url(),
            reverse("read-later"),
        ):
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), "favicon.ico")

    def test_root_favicon_ico_redirects_to_the_static_file(self):
        response = self.client.get("/favicon.ico")

        self.assertEqual(response.status_code, 301)
        self.assertIn("favicon.ico", response["Location"])
