"""Tests for the Kyushu seed data and its two management commands."""

import json
import shutil
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils.text import slugify
from PIL import Image

from blog import credits
from blog.management.commands.fetch_seed_photos import (
    _plain,
    _slugify_filename,
    is_free_licence,
)
from blog.models import FocalPoint, Post, PostImage, Tag
from blog.seed_data import POSTS

from .factories import make_gallery_image, make_post

MEDIA_ROOT = tempfile.mkdtemp(prefix="blog-seed-media-")


def _commons_titles():
    for spec in POSTS:
        yield spec["image"]
        for name, _caption, *_rest in spec["gallery"]:
            yield name


class SeedDataTests(TestCase):
    """The data module alone, before anything touches the database."""

    def test_covers_every_kyushu_prefecture(self):
        tags = {tag for spec in POSTS for tag in spec["tags"]}
        for prefecture in (
            "Oita",
            "Fukuoka",
            "Kumamoto",
            "Nagasaki",
            "Kagoshima",
            "Miyazaki",
            "Saga",
        ):
            self.assertIn(prefecture, tags)

    def test_at_least_ten_posts(self):
        self.assertGreaterEqual(len(POSTS), 10)

    def test_slugs_and_titles_are_unique(self):
        slugs = [spec["slug"] for spec in POSTS]
        self.assertEqual(len(slugs), len(set(slugs)))
        titles = [spec["title"] for spec in POSTS]
        self.assertEqual(len(titles), len(set(titles)))

    def test_slugs_match_their_titles(self):
        # A hand-written slug that has drifted from its title is a silent SEO
        # problem, so keep the two tied together.
        for spec in POSTS:
            self.assertIn(slugify(spec["title"])[:40], spec["slug"] + "-")

    def test_fields_fit_the_model_columns(self):
        for spec in POSTS:
            with self.subTest(slug=spec["slug"]):
                self.assertLessEqual(len(spec["title"]), 150)
                self.assertLessEqual(len(spec["excerpt"]), 200)
                self.assertLessEqual(len(spec["slug"]), 100)
                for tag in spec["tags"]:
                    self.assertLessEqual(len(tag), 20)
                for _name, caption, *_rest in spec["gallery"]:
                    self.assertLessEqual(len(caption), 200)

    def test_every_post_has_a_header_and_a_gallery(self):
        for spec in POSTS:
            with self.subTest(slug=spec["slug"]):
                self.assertTrue(spec["image"])
                self.assertGreaterEqual(len(spec["gallery"]), 2)

    def test_gallery_focal_points_are_valid_choices(self):
        valid = {value for value, _label in FocalPoint.choices}
        for spec in POSTS:
            with self.subTest(slug=spec["slug"]):
                self.assertIn(spec["focal_point"], valid)
                for entry in spec["gallery"]:
                    if len(entry) > 2:
                        self.assertIn(entry[2], valid)

    def test_publish_dates_are_distinct_and_parseable(self):
        from datetime import datetime

        dates = [datetime.strptime(s["published"], "%Y-%m-%d %H:%M") for s in POSTS]
        self.assertEqual(len(dates), len(set(dates)))


class PhotoHelperTests(TestCase):
    def test_commons_html_is_reduced_to_text(self):
        self.assertEqual(
            _plain('<a href="/x" title="y">Jane &amp; Co</a>'), "Jane & Co"
        )

    def test_local_filenames_are_url_safe(self):
        name = _slugify_filename("Beppu Umi-jigoku04n4272.jpg")
        self.assertEqual(name, "beppu-umi-jigoku04n4272.jpg")

    def test_non_free_licences_are_not_allowed(self):
        for licence in ("All rights reserved", "Fair use", "", None):
            with self.subTest(licence=licence):
                self.assertFalse(is_free_licence(licence))

    def test_non_commercial_and_no_derivative_licences_are_not_allowed(self):
        # These start with "CC BY" but forbid what this blog does with the
        # photo: NC forbids commercial use, ND forbids the resized copy.
        for licence in ("CC BY-NC 4.0", "CC BY-ND 2.0", "CC BY-NC-SA 3.0"):
            with self.subTest(licence=licence):
                self.assertFalse(is_free_licence(licence))

    def test_free_licences_are_allowed(self):
        for licence in ("CC0", "CC BY 2.5", "CC BY-SA 4.0", "Public domain"):
            with self.subTest(licence=licence):
                self.assertTrue(is_free_licence(licence))


# A small limit and small fixtures keep 39 images per seed run cheap while
# still exercising the downscale: the fixtures are 600px, the limit is 400.
@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    IMAGE_UPLOAD={
        "max_dimension": 400,
        "jpeg_quality": 70,
        # Must be a complete dict: the settings module always supplies every
        # key, so the code reads them directly rather than defensively.
        "thumbnail_width": 200,
        "srcset_widths": [100, 200],
    },
)
class SeedCommandTests(TestCase):
    """The seeding command, run against a fake photo directory."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.photo_dir = Path(tempfile.mkdtemp(prefix="blog-seed-photos-"))
        credits = {}
        for title in dict.fromkeys(_commons_titles()):
            local = _slugify_filename(title)
            Image.new("RGB", (600, 400), (40, 90, 140)).save(cls.photo_dir / local)
            credits[title] = {
                "file": local,
                "artist": "A Photographer",
                "licence": "CC BY-SA 4.0",
                "licence_url": "https://creativecommons.org/licenses/by-sa/4.0",
                "source": f"https://commons.wikimedia.org/wiki/File:{title}",
            }
        (cls.photo_dir / "credits.json").write_text(json.dumps(credits))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.photo_dir, ignore_errors=True)
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Seeding writes blog/photo_credits.json; send it to the throwaway
        # directory so a test run never touches the file in the repo.
        patch = mock.patch.object(
            credits, "ATTRIBUTIONS_PATH", self.photo_dir / "photo_credits.json"
        )
        patch.start()
        self.addCleanup(patch.stop)

    def seed(self, **kwargs):
        call_command(
            "seed_kyushu", photos=str(self.photo_dir), stdout=StringIO(), **kwargs
        )

    def test_it_creates_every_post_published_with_pictures(self):
        self.seed()

        self.assertEqual(Post.objects.published().count(), len(POSTS))
        for spec in POSTS:
            with self.subTest(slug=spec["slug"]):
                post = Post.objects.get(slug=spec["slug"])
                self.assertEqual(post.title, spec["title"])
                self.assertTrue(post.image.name)
                self.assertTrue(post.image_width and post.image_height)
                self.assertEqual(post.gallery.count(), len(spec["gallery"]))
                self.assertEqual(
                    sorted(t.caption for t in post.tags.all()), sorted(spec["tags"])
                )

    def test_publish_dates_come_from_the_data_not_from_now(self):
        self.seed()
        post = Post.objects.get(slug="the-steaming-streets-of-beppu")
        self.assertEqual(post.published_at.strftime("%Y-%m-%d"), "2025-01-18")

    def test_uploads_are_compressed_through_the_normal_pipeline(self):
        # The fixtures are 600px wide, over the limit set on this class, so a
        # seeded picture that comes back at 600 means the resize was skipped.
        self.seed()
        limit = settings.IMAGE_UPLOAD["max_dimension"]

        for post in Post.objects.all():
            with self.subTest(slug=post.slug):
                self.assertTrue(post.image.name.endswith(".jpg"))
                self.assertLessEqual(max(post.image_width, post.image_height), limit)
                with Image.open(post.image.path) as opened:
                    self.assertLessEqual(max(opened.size), limit)

        for picture in PostImage.objects.all():
            with self.subTest(gallery=picture.pk):
                self.assertLessEqual(
                    max(picture.image_width, picture.image_height), limit
                )

    def test_replace_removes_tags_that_no_longer_have_posts(self):
        make_post("Old", slug="old", tags=[Tag.objects.create(caption="Leftover")])

        self.seed(replace=True)

        self.assertFalse(Tag.objects.filter(caption="Leftover").exists())
        self.assertTrue(Tag.objects.filter(caption="Oita").exists())

    def test_post_bodies_carry_no_credit_list(self):
        # Attribution belongs on the credits page, not under every article.
        self.seed()
        for post in Post.objects.all():
            with self.subTest(slug=post.slug):
                self.assertNotIn("Photo credits", post.content)
                self.assertNotIn("commons.wikimedia.org", post.content)
                self.assertNotIn("A Photographer", post.content)

    def test_every_seeded_picture_is_credited(self):
        self.seed()

        rows = {row["file"] for row in credits.load()}
        stored = {p.image.name for p in Post.objects.all()}
        stored |= {i.image.name for i in PostImage.objects.all()}
        self.assertEqual(rows, stored)

    def test_a_gallery_photo_may_override_the_post_focal_point(self):
        # The gallery crops to a wide letterbox, so a picture whose subject
        # sits high in the frame needs "top" even when the header wants
        # "center". Without the override the Peace Statue loses its head.
        self.seed()

        post = Post.objects.get(slug="a-quiet-day-in-nagasaki")
        statue = post.gallery.first()
        self.assertEqual(post.focal_point, FocalPoint.CENTER)
        self.assertEqual(statue.focal_point, FocalPoint.TOP)

    def test_a_gallery_photo_without_one_inherits_the_post_focal_point(self):
        self.seed()

        post = Post.objects.get(slug="the-steaming-streets-of-beppu")
        for picture in post.gallery.all():
            self.assertEqual(picture.focal_point, post.focal_point)

    def test_credits_record_the_photographer_and_licence(self):
        self.seed()

        row = credits.load()[0]
        self.assertEqual(row["artist"], "A Photographer")
        self.assertEqual(row["licence"], "CC BY-SA 4.0")
        self.assertTrue(row["source"].startswith("https://commons.wikimedia.org/"))
        self.assertTrue(row["post_url"].startswith("/posts/"))

    def test_without_replace_existing_posts_survive(self):
        make_post("Something I Wrote Earlier", slug="earlier")
        self.seed()
        self.assertTrue(Post.objects.filter(slug="earlier").exists())

    def test_replace_clears_existing_posts_and_their_gallery(self):
        old = make_post("Something I Wrote Earlier", slug="earlier")
        make_gallery_image(old)

        self.seed(replace=True)

        self.assertFalse(Post.objects.filter(slug="earlier").exists())
        self.assertEqual(Post.objects.count(), len(POSTS))
        self.assertEqual(
            PostImage.objects.count(), sum(len(s["gallery"]) for s in POSTS)
        )

    def test_running_twice_with_replace_is_idempotent(self):
        self.seed(replace=True)
        self.seed(replace=True)
        self.assertEqual(Post.objects.count(), len(POSTS))
        self.assertEqual(Tag.objects.filter(caption="Oita").count(), 1)

    def test_a_missing_photo_directory_is_a_clear_error(self):
        with self.assertRaisesMessage(CommandError, "fetch_seed_photos"):
            call_command("seed_kyushu", photos="/nowhere/at/all", stdout=StringIO())

    def test_seeded_posts_render(self):
        self.seed(replace=True)
        for spec in POSTS[:3]:
            with self.subTest(slug=spec["slug"]):
                response = self.client.get(f"/posts/{spec['slug']}")
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, spec["title"])

    def test_the_archive_paginates_the_seeded_posts(self):
        self.seed(replace=True)
        response = self.client.get("/posts")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["posts"]), 6)
        self.assertTrue(response.context["page_obj"].has_next())
