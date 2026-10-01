"""The repair path for a database that came back without its photographs."""

import shutil
import tempfile
from io import StringIO
from pathlib import Path

from django.core.files.storage import default_storage
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from .factories import make_gallery_image, make_image_file, make_post

MEDIA_ROOT = tempfile.mkdtemp(prefix="blog-restore-media-")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class RestoreMediaTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.photos = Path(tempfile.mkdtemp(prefix="blog-restore-src-"))
        self.addCleanup(shutil.rmtree, self.photos, True)

        self.post = make_post("Lost Pictures", image=make_image_file("beppu.jpg"))
        self.gallery = make_gallery_image(
            self.post, image=make_image_file("street.jpg")
        )

    def _run(self, **options):
        out = StringIO()
        call_command(
            "restore_media", photos=str(self.photos), stdout=out, stderr=out, **options
        )
        return out.getvalue()

    def _put_source(self, stored_name):
        """Write a usable source photograph for an image the site has lost."""
        source = self.photos / Path(stored_name).name
        source.write_bytes(make_image_file(source.name).read())
        return source

    def _delete_from_storage(self, name):
        default_storage.delete(name)
        self.assertFalse(default_storage.exists(name))

    def test_it_does_nothing_when_every_picture_is_present(self):
        output = self._run()

        self.assertIn("nothing to do", output)
        self.assertTrue(default_storage.exists(self.post.image.name))

    def test_a_lost_picture_is_put_back(self):
        name = self.post.image.name
        self._put_source(name)
        self._delete_from_storage(name)

        self._run()

        self.assertTrue(default_storage.exists(name))

    def test_the_row_keeps_pointing_at_the_same_path(self):
        # The whole point: a restored file under a new name would leave the
        # page asking for something that still isn't there.
        name = self.post.image.name
        self._put_source(name)
        self._delete_from_storage(name)

        self._run()

        self.post.refresh_from_db()
        self.assertEqual(self.post.image.name, name)

    def test_gallery_pictures_are_restored_too(self):
        name = self.gallery.image.name
        self._put_source(name)
        self._delete_from_storage(name)

        self._run()

        self.assertTrue(default_storage.exists(name))

    def test_dry_run_reports_without_uploading(self):
        name = self.post.image.name
        self._put_source(name)
        self._delete_from_storage(name)

        output = self._run(dry_run=True)

        self.assertIn(f"would restore {name}", output)
        self.assertFalse(default_storage.exists(name))

    def test_a_picture_with_no_source_is_reported_not_crashed_on(self):
        name = self.post.image.name
        self._delete_from_storage(name)  # no source written

        output = self._run()

        self.assertIn("no source photograph", output)
        self.assertFalse(default_storage.exists(name))

    def test_one_missing_source_does_not_stop_the_others(self):
        lost = self.post.image.name
        also_lost = self.gallery.image.name
        self._put_source(also_lost)  # only the gallery one has a source
        self._delete_from_storage(lost)
        self._delete_from_storage(also_lost)

        self._run()

        self.assertTrue(default_storage.exists(also_lost))
        self.assertFalse(default_storage.exists(lost))

    def test_a_restored_picture_goes_through_the_resize_pipeline(self):
        # Restoring must not drop a full-resolution original into storage;
        # the database's stored width would then describe a different file.
        from django.conf import settings

        limit = settings.IMAGE_UPLOAD["max_dimension"]
        name = self.post.image.name
        source = self.photos / Path(name).name
        source.write_bytes(
            make_image_file(source.name, size=(limit * 2, limit * 2)).read()
        )
        self._delete_from_storage(name)

        self._run()

        self.post.refresh_from_db()
        self.assertLessEqual(self.post.image.width, limit)

    def test_it_refuses_to_leave_the_row_pointing_somewhere_new(self):
        # Storage is free to hand back a different name than it was given.
        # Silently accepting that would leave the row pointing at one path and
        # the restored bytes sitting at another, which looks like a success
        # and still renders a broken picture.
        name = self.post.image.name
        self._put_source(name)
        self._delete_from_storage(name)

        with _StorageRenamesOnSave(suffix=".moved"):
            with self.assertRaises(CommandError):
                self._run()


class _StorageRenamesOnSave:
    """Make storage file everything under a different name than it was asked.

    Faking this through ``exists`` instead would hang: FileSystemStorage asks
    again on a name collision, and a storage that always calls the path free
    sends it round that loop forever.
    """

    def __init__(self, suffix):
        self.suffix = suffix

    def __enter__(self):
        self.original = default_storage.save

        def save(name, content, max_length=None):
            return self.original(name + self.suffix, content, max_length)

        default_storage.save = save

    def __exit__(self, *exc):
        default_storage.save = self.original
