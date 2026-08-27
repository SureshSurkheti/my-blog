"""Site icons: present in the markup, served, and valid image files."""

import json
import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings
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

    @staticmethod
    def _mark(image):
        """Columns and rows covered by the light mark sitting on the tile."""
        width, height = image.size
        pixels = image.load()
        found = [
            (x, y)
            for y in range(height)
            for x in range(width)
            if pixels[x, y][3] > 128 and min(pixels[x, y][:3]) > 180
        ]
        return found

    def test_every_icon_actually_has_its_mark_on_it(self):
        for name in ("favicon-32.png", "icon-192.png", "icon-512.png"):
            with self.subTest(icon=name):
                image = Image.open(STATIC / name).convert("RGBA")

                self.assertTrue(
                    self._mark(image), f"{name} is a bare tile with no mark on it"
                )

    def test_the_mark_sits_in_the_middle_of_the_tile(self):
        """An off-centre mark reads as a mistake at any size.

        Deliberately not asserting how *large* the mark is. It spans about a
        third of the tile, which is on the small side for a 16px favicon — but
        that is the supplied artwork's decision to make, and font-size in
        static/favicon.svg is the one place to change it.
        """
        for name in ("favicon-32.png", "icon-192.png", "icon-512.png"):
            with self.subTest(icon=name):
                image = Image.open(STATIC / name).convert("RGBA")
                width, height = image.size
                found = self._mark(image)
                xs = [x for x, _ in found]
                offset = abs((min(xs) + max(xs)) / 2 - width / 2) / width

                self.assertLess(
                    offset,
                    0.04,
                    f"the mark in {name} is {offset:.0%} of the width off centre",
                )

    def test_manifest_is_valid_json_and_points_at_real_files(self):
        # Read as rendered, not off disk: the manifest is a template now, so
        # the file on disk is not what a browser receives.
        manifest = json.loads(self.client.get("/site.webmanifest").content)

        self.assertEqual(manifest["name"], "Suresh's Blog")
        for icon in manifest["icons"]:
            name = icon["src"].rsplit("/", 1)[-1]
            with self.subTest(icon=name):
                self.assertTrue((STATIC / name).exists())

    def test_the_theme_colour_matches_the_icon(self):
        manifest = json.loads(self.client.get("/site.webmanifest").content)
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


STATIC_ROOT = tempfile.mkdtemp(prefix="blog-manifest-static-")


@override_settings(
    STATIC_ROOT=STATIC_ROOT,
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "my_site.settings.SilentManifestStaticFilesStorage"},
    },
)
class WebManifestTests(TestCase):
    """The PWA manifest, under the hashed-filename storage production uses.

    Collects the static files for real: the bug being guarded only appears
    once filenames carry a content hash, so testing against the plain
    development storage would prove nothing.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with override_settings(
            STATIC_ROOT=STATIC_ROOT,
            STORAGES={
                "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                "staticfiles": {
                    "BACKEND": "my_site.settings.SilentManifestStaticFilesStorage"
                },
            },
        ):
            call_command("collectstatic", "--no-input", verbosity=0)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(STATIC_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_the_manifest_is_served_as_json(self):
        response = self.client.get("/site.webmanifest")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/manifest+json")
        json.loads(response.content)

    def test_every_icon_it_names_is_a_hashed_file_that_exists(self):
        """The bug this guards.

        Production renames static files with a content hash. Django rewrites
        such references inside CSS but not inside a manifest, so a hard-coded
        "/static/icon-192.png" 404s on the live site while working perfectly
        in development.
        """
        icons = json.loads(self.client.get("/site.webmanifest").content)["icons"]

        self.assertTrue(icons, "the manifest lists no icons at all")
        for icon in icons:
            with self.subTest(icon=icon["src"]):
                relative = icon["src"].removeprefix(settings.STATIC_URL)
                self.assertRegex(relative, r"\.[0-9a-f]{12}\.png$")
                self.assertTrue(
                    (Path(STATIC_ROOT) / relative).exists(),
                    f"{icon['src']} is named but was never collected",
                )

    def test_the_page_links_the_rendered_manifest(self):
        response = self.client.get("/")

        self.assertContains(response, 'rel="manifest" href="/site.webmanifest"')
