"""Tests for comment moderation, the post gallery and upload processing."""

import shutil
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from blog.imaging import optimize_uploaded_image
from blog.models import Comment, FocalPoint, Post, PostImage

from .factories import (
    make_comment,
    make_gallery_image,
    make_image_file,
    make_post,
)

# Uploads in these tests go to a throwaway directory, never the real uploads/.
MEDIA_ROOT = tempfile.mkdtemp(prefix="blog-test-media-")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class CommentModerationTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.post = make_post("Moderated")

    def test_new_comments_start_unapproved(self):
        self.client.post(
            self.post.get_absolute_url(),
            {"user_name": "Ada", "user_email": "ada@example.com", "text": "Hello!"},
        )
        comment = Comment.objects.get()
        self.assertFalse(comment.is_approved)

    def test_unapproved_comments_are_hidden_from_the_page(self):
        make_comment(self.post, "Pending", text="Not yet visible.", approved=False)
        make_comment(self.post, "Live", text="Definitely visible.", approved=True)

        response = self.client.get(self.post.get_absolute_url())

        self.assertContains(response, "Definitely visible.")
        self.assertNotContains(response, "Not yet visible.")
        self.assertContains(response, "1 Comment")

    def test_submitter_is_told_the_comment_awaits_approval(self):
        response = self.client.post(
            self.post.get_absolute_url(),
            {"user_name": "Ada", "user_email": "ada@example.com", "text": "Hello!"},
            follow=True,
        )
        self.assertContains(response, "will appear once approved")

    def test_approving_makes_a_comment_visible(self):
        comment = make_comment(self.post, text="Now you see me.", approved=False)

        comment.is_approved = True
        comment.save()

        response = self.client.get(self.post.get_absolute_url())
        self.assertContains(response, "Now you see me.")

    def test_approved_queryset(self):
        make_comment(self.post, approved=True)
        make_comment(self.post, approved=False)
        self.assertEqual(Comment.objects.approved().count(), 1)

    def test_admin_approve_action(self):
        pending = make_comment(self.post, approved=False)
        User.objects.create_superuser("root", "root@example.com", "pw12345!")
        self.client.login(username="root", password="pw12345!")

        self.client.post(
            reverse("admin:blog_comment_changelist"),
            {"action": "approve_selected", "_selected_action": [pending.pk]},
            follow=True,
        )

        pending.refresh_from_db()
        self.assertTrue(pending.is_approved)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class HoneypotTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.post = make_post("Spam target")

    def test_filled_honeypot_is_discarded_without_an_error(self):
        response = self.client.post(
            self.post.get_absolute_url(),
            {
                "user_name": "Bot",
                "user_email": "bot@example.com",
                "text": "Buy cheap things",
                "website": "http://spam.example.com",
            },
        )

        self.assertRedirects(response, self.post.get_absolute_url())
        self.assertEqual(Comment.objects.count(), 0)

    def test_empty_honeypot_lets_a_real_comment_through(self):
        self.client.post(
            self.post.get_absolute_url(),
            {
                "user_name": "Ada",
                "user_email": "ada@example.com",
                "text": "A real comment",
                "website": "",
            },
        )
        self.assertEqual(Comment.objects.count(), 1)

    def test_the_field_is_hidden_from_readers(self):
        response = self.client.get(self.post.get_absolute_url())
        self.assertContains(response, 'class="honeypot"')


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class GalleryTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.post = make_post("Trip to Beppu")

    def test_gallery_photos_appear_on_the_post_page(self):
        make_gallery_image(self.post, caption="Steam rising over the town")

        response = self.client.get(self.post.get_absolute_url())

        self.assertContains(response, "Steam rising over the town")
        self.assertContains(response, 'id="gallery"')

    def test_no_gallery_section_without_photos(self):
        response = self.client.get(self.post.get_absolute_url())
        self.assertNotContains(response, 'id="gallery"')

    def test_photos_are_ordered_by_sort_order(self):
        second = make_gallery_image(self.post, caption="Second", sort_order=2)
        first = make_gallery_image(self.post, caption="First", sort_order=1)

        self.assertEqual(list(self.post.gallery.all()), [first, second])

    def test_deleting_a_post_removes_its_gallery(self):
        make_gallery_image(self.post)
        self.post.delete()
        self.assertEqual(PostImage.objects.count(), 0)

    def test_a_caption_is_optional(self):
        photo = make_gallery_image(self.post, caption="")
        self.assertIn("Image", str(photo))


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ImageProcessingTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_large_uploads_are_scaled_down(self):
        limit = settings.IMAGE_UPLOAD["max_dimension"]
        post = make_post("Huge photo", image=make_image_file(size=(4000, 3000)))

        with Image.open(post.image.path) as stored:
            self.assertEqual(max(stored.size), limit)
            # 4:3 in, 4:3 out — the aspect ratio is preserved.
            self.assertEqual(stored.size, (limit, int(limit * 0.75)))

    def test_small_uploads_are_not_upscaled(self):
        post = make_post("Small photo", image=make_image_file(size=(400, 300)))

        with Image.open(post.image.path) as stored:
            self.assertEqual(stored.size, (400, 300))

    def test_uploads_are_compressed(self):
        original = make_image_file(size=(2600, 2000))
        original_size = original.size

        post = make_post("Compressed", image=original)

        self.assertLess(post.image.size, original_size)

    def test_png_without_transparency_becomes_a_jpeg(self):
        post = make_post("Opaque png", image=make_image_file("shot.png", fmt="PNG"))
        self.assertTrue(post.image.name.endswith(".jpg"))

    def test_transparency_is_preserved_as_png(self):
        from io import BytesIO

        from django.core.files.uploadedfile import SimpleUploadedFile

        buffer = BytesIO()
        Image.new("RGBA", (500, 500), (255, 0, 0, 0)).save(buffer, format="PNG")
        upload = SimpleUploadedFile(
            "logo.png", buffer.getvalue(), content_type="image/png"
        )

        post = make_post("Transparent", image=upload)

        self.assertTrue(post.image.name.endswith(".png"))
        with Image.open(post.image.path) as stored:
            self.assertEqual(stored.mode, "RGBA")

    def test_exif_metadata_is_stripped(self):
        post = make_post("Geotagged", image=make_image_file(size=(1200, 900)))

        with Image.open(post.image.path) as stored:
            self.assertFalse(stored.getexif())

    def test_editing_a_post_does_not_reprocess_the_stored_file(self):
        post = make_post("Stable", image=make_image_file(size=(3000, 2000)))
        name_before = post.image.name

        post.title = "Stable, renamed"
        post.save()

        post.refresh_from_db()
        self.assertEqual(post.image.name, name_before)

    def test_gallery_uploads_are_processed_too(self):
        post = make_post("With gallery")
        photo = make_gallery_image(post, image=make_image_file(size=(3500, 2500)))

        with Image.open(photo.image.path) as stored:
            self.assertLessEqual(
                max(stored.size), settings.IMAGE_UPLOAD["max_dimension"]
            )

    def test_a_post_without_an_image_saves_cleanly(self):
        self.assertIsNone(optimize_uploaded_image(None) or None)
        post = make_post("No picture")
        self.assertFalse(post.image)


class FocalPointTests(TestCase):
    def test_default_keeps_the_top_of_the_picture(self):
        post = make_post("Top kept")
        self.assertEqual(post.focal_point, FocalPoint.TOP)
        # 0% vertical = the top edge is never trimmed.
        self.assertEqual(post.focal_css, "50% 0%")

    def test_each_choice_maps_to_a_css_position(self):
        """The two percentages are the horizontal and vertical anchor.

        50% on an axis means that axis is centred, so any overflow there is
        trimmed evenly off *both* of its edges; 0%/100% pins that edge so the
        whole trim comes off the opposite one. TOP is therefore "50% 0%":
        sides trimmed evenly, bottom trimmed, top never.
        """
        expected = {
            FocalPoint.CENTER: "50% 50%",
            FocalPoint.TOP: "50% 0%",
            FocalPoint.BOTTOM: "50% 100%",
            FocalPoint.LEFT: "0% 50%",
            FocalPoint.RIGHT: "100% 50%",
        }
        for value, css in expected.items():
            with self.subTest(focal_point=value):
                self.assertEqual(FocalPoint.to_css(value), css)

    def test_unknown_value_falls_back_to_center(self):
        self.assertEqual(FocalPoint.to_css("nonsense"), "50% 50%")

    @override_settings(MEDIA_ROOT=MEDIA_ROOT)
    def test_focal_point_reaches_the_rendered_card(self):
        make_post(
            "Trimmed",
            image=make_image_file(),
            focal_point=FocalPoint.BOTTOM,
        )

        response = self.client.get(reverse("posts-page"))

        self.assertContains(response, "object-position: 50% 100%")
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


class PostQuerySetGalleryTests(TestCase):
    def test_gallery_is_prefetched_on_the_detail_page(self):
        post = make_post("Prefetched")
        # Post (+author joined), tags, gallery, the newer/older neighbours, and
        # approved comments — and no extra query per gallery photo.
        with self.assertNumQueries(6):
            self.client.get(post.get_absolute_url())
        self.assertEqual(Post.objects.count(), 1)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class BodyImageTests(TestCase):
    """Pictures placed inside the post body via Markdown."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_markdown_image_in_the_body_is_rendered(self):
        post = make_post(
            "Illustrated",
            content="Here is the view:\n\n![The bay at dusk](/files/posts/bay.jpg)",
        )

        response = self.client.get(post.get_absolute_url())

        self.assertContains(response, 'src="/files/posts/bay.jpg"')
        self.assertContains(response, 'alt="The bay at dusk"')

    def test_admin_offers_a_paste_ready_snippet(self):
        from blog.admin import markdown_snippet

        post = make_post("Snippet", image=make_image_file())
        snippet = markdown_snippet(post.image, post.title)

        self.assertIn("![Snippet](", snippet)
        self.assertIn(post.image.url, snippet)

    def test_snippet_is_blank_without_an_image(self):
        from blog.admin import markdown_snippet

        self.assertEqual(markdown_snippet(None), "—")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class GalleryLightboxTests(TestCase):
    """The gallery viewer degrades to plain links when JavaScript is off."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.post = make_post("Photo trip")

    def test_gallery_markup_carries_the_viewer_hooks(self):
        make_gallery_image(self.post, caption="First stop")

        response = self.client.get(self.post.get_absolute_url())

        self.assertContains(response, "data-gallery")
        self.assertContains(response, "data-gallery-item")
        self.assertContains(response, 'data-caption="First stop"')

    def test_thumbnails_still_link_to_the_full_file(self):
        photo = make_gallery_image(self.post)
        response = self.client.get(self.post.get_absolute_url())
        self.assertContains(response, f'href="{photo.image.url}"')

    def test_viewer_script_is_loaded_only_when_there_are_photos(self):
        without = self.client.get(self.post.get_absolute_url())
        self.assertNotContains(without, "gallery.js")

        make_gallery_image(self.post)

        with_photos = self.client.get(self.post.get_absolute_url())
        self.assertContains(with_photos, "gallery.js")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ConfigurableCompressionTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_max_dimension_comes_from_settings(self):
        with self.settings(IMAGE_UPLOAD={"max_dimension": 800, "jpeg_quality": 80}):
            post = make_post("Tighter", image=make_image_file(size=(2400, 1800)))

        with Image.open(post.image.path) as stored:
            self.assertEqual(max(stored.size), 800)

    def test_lower_quality_produces_a_smaller_file(self):
        with self.settings(IMAGE_UPLOAD={"max_dimension": 1600, "jpeg_quality": 95}):
            high = make_post("High", image=make_image_file(size=(1600, 1200)))
        with self.settings(IMAGE_UPLOAD={"max_dimension": 1600, "jpeg_quality": 40}):
            low = make_post("Low", image=make_image_file(size=(1600, 1200)))

        self.assertLess(low.image.size, high.image.size)

    def test_default_settings_are_applied_without_explicit_arguments(self):
        post = make_post("Defaults", image=make_image_file(size=(3000, 2000)))

        with Image.open(post.image.path) as stored:
            self.assertEqual(max(stored.size), 1600)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class CardSizingTests(TestCase):
    """Cards must fill their grid column regardless of how short the text is."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_every_card_picture_asks_to_keep_the_top(self):
        make_post("Short one", excerpt="new", image=make_image_file())
        make_post(
            "Long one",
            excerpt="A much longer excerpt that wraps onto several lines here.",
            image=make_image_file(),
        )

        response = self.client.get(reverse("posts-page"))
        body = response.content.decode()

        # Both cards render the same picture directive, so both boxes match.
        self.assertEqual(body.count("object-position: 50% 0%"), 2)
        self.assertNotIn("object-position: 50% 50%", body)

    def test_gallery_photos_default_to_keeping_the_top(self):
        post = make_post("With photos")
        photo = make_gallery_image(post)
        self.assertEqual(photo.focal_css, "50% 0%")

    def test_an_explicit_focal_point_still_wins(self):
        post = make_post("Bottom kept", focal_point=FocalPoint.BOTTOM)
        self.assertEqual(post.focal_css, "50% 100%")
