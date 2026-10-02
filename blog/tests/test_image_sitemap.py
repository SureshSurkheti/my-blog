"""Photographs in the sitemap, which is how Google finds images it hasn't crawled."""

import shutil
import tempfile

from django.test import TestCase, override_settings

from blog.sitemaps import sitemap_images

from .factories import make_gallery_image, make_image_file, make_post

MEDIA_ROOT = tempfile.mkdtemp(prefix="blog-image-sitemap-")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ImageSitemapTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def body(self):
        return self.client.get("/sitemap.xml").content.decode()

    def test_a_posts_header_picture_is_listed(self):
        make_post("Beppu Steam", image=make_image_file("beppu.jpg"))

        self.assertIn("<image:image>", self.body())

    def test_the_header_picture_is_captioned_with_the_title(self):
        # A header image has no caption of its own, and Google shows the
        # caption beside the picture, so the title is the honest stand-in.
        make_post("Beppu Steam", image=make_image_file("beppu.jpg"))

        self.assertIn("<image:caption>Beppu Steam</image:caption>", self.body())

    def test_gallery_pictures_are_listed_with_their_own_captions(self):
        post = make_post("Beppu Steam", image=make_image_file("beppu.jpg"))
        make_gallery_image(post, caption="Steam off the street")

        body = self.body()

        self.assertIn("<image:caption>Steam off the street</image:caption>", body)
        self.assertEqual(body.count("<image:image>"), 2)

    def test_a_post_with_no_picture_adds_nothing(self):
        make_post("Words Only")

        self.assertNotIn("<image:image>", self.body())

    def test_a_draft_contributes_no_pictures(self):
        make_post("Hidden", published=False, image=make_image_file("secret.jpg"))

        self.assertNotIn("<image:image>", self.body())

    def test_the_namespace_is_declared(self):
        # Without the declaration the image tags are ignored entirely.
        make_post("Beppu Steam", image=make_image_file("beppu.jpg"))

        self.assertIn(
            'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"',
            self.body(),
        )

    def test_the_document_is_still_well_formed(self):
        post = make_post("Beppu Steam", image=make_image_file("beppu.jpg"))
        make_gallery_image(post, caption="Steam & sulphur <everywhere>")

        import xml.dom.minidom

        xml.dom.minidom.parseString(self.body())  # raises if it is not

    def test_relative_urls_are_made_absolute(self):
        # Local storage returns /files/...; a sitemap must carry full URLs.
        post = make_post("Beppu Steam", image=make_image_file("beppu.jpg"))

        entries = sitemap_images(post, "https", "example.com")

        self.assertTrue(entries[0]["loc"].startswith("https://example.com/"))

    def test_an_already_absolute_url_is_left_alone(self):
        # Cloudinary hands back a full URL; prefixing it would corrupt it.
        post = make_post("Beppu Steam", image=make_image_file("beppu.jpg"))
        post.image.name = "x"

        class Remote:
            url = "https://res.cloudinary.com/demo/image/upload/v1/beppu.jpg"

        entries = sitemap_images(
            type("P", (), {"image": Remote(), "title": "T", "gallery": post.gallery})(),
            "https",
            "example.com",
        )

        self.assertEqual(entries[0]["loc"], Remote.url)


class SitemapInternalsTests(TestCase):
    def test_django_still_hands_us_the_object_on_each_entry(self):
        """PostSitemap._urls leans on Django's own private method.

        If a Django upgrade stops putting the model instance on each entry, or
        renames _urls, the images vanish silently and nobody notices for
        months. This fails instead.
        """
        from blog.sitemaps import PostSitemap

        make_post("Mapped")
        urls = PostSitemap()._urls(page=1, protocol="https", domain="example.com")

        self.assertTrue(urls)
        self.assertIn("item", urls[0])
        self.assertIn("images", urls[0])
