"""Re-upload the pictures the database points at but storage no longer holds.

A restored database carries image *paths*, not image *files*. ``loaddata``
rebuilds every row and nothing puts the photographs back, so the posts render
perfectly while each picture 404s — which is exactly how the site came back up
after its database was rebuilt, with no photographs on it.

This compares what the database references against what storage actually has
and re-uploads only the gaps. Once the files are in place it does nothing, so
it is safe to run on every deploy.

The bytes go through the model's own save path rather than straight at the
storage backend, so a restored picture is resized and re-encoded by the same
pipeline as a fresh upload instead of landing at full camera resolution.

Storage is allowed to file a picture under a different name than it was asked
for, and Cloudinary always does: it drops the extension and appends a random
suffix, so ``posts/beppu.jpg`` comes back as ``files/posts/beppu_a1b2c3``.
That is also why the fixture's paths never match a Cloudinary account in the
first place — content.json is dumped from a local database, where storage is
the filesystem and the names stay clean. Saving the instance writes whatever
name came back, so the row and the bytes stay together.
"""

from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import BaseCommand

from blog.models import Post, PostImage

CONTENT_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}


class Command(BaseCommand):
    help = "Re-upload any picture the database references but storage has lost."

    def add_arguments(self, parser):
        parser.add_argument(
            "--photos",
            default="seed_photos",
            help="Directory holding the source photographs (default: seed_photos).",
        )
        parser.add_argument(
            "--fetch",
            action="store_true",
            help="Download the seed photographs first if they aren't on disk.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what is missing without uploading anything.",
        )

    def handle(self, *args, **options):
        photo_dir = Path(options["photos"])
        dry_run = options["dry_run"]

        missing = [
            (instance, field, file.name)
            for instance, field, file in self._pictures()
            if not file.storage.exists(file.name)
        ]

        if not missing:
            self.stdout.write("Every picture is present in storage — nothing to do.")
            return

        self.stdout.write(f"{len(missing)} picture(s) missing from storage.")

        # Only worth the network round trip once we know something is missing;
        # a healthy deploy should never download 30MB of photographs.
        if options["fetch"] and not self._sources_complete(missing, photo_dir):
            self.stdout.write("Fetching the source photographs…")
            call_command("fetch_seed_photos", photos=str(photo_dir))

        restored, unresolved, failed = 0, [], []
        for instance, field, name in missing:
            source = photo_dir / Path(name).name
            if not source.exists():
                unresolved.append(name)
                continue

            if dry_run:
                self.stdout.write(f"  would restore {name}")
                restored += 1
                continue

            # One picture that will not upload must not cost the site the
            # other thirty-eight, and must not fail the deploy either: a post
            # missing its photograph is still a post worth serving.
            try:
                setattr(instance, field, self._upload(source))
                instance.save()
            except Exception as problem:  # noqa: BLE001 - reported, not swallowed
                failed.append((name, problem))
                self.stderr.write(f"  could not restore {name}: {problem}")
                continue

            stored = getattr(instance, field).name
            if stored == name:
                self.stdout.write(f"  restored {name}")
            else:
                self.stdout.write(f"  restored {name} as {stored}")
            restored += 1

        self.stdout.write(
            f"{restored} restored, {len(unresolved)} without a source, "
            f"{len(failed)} failed."
        )
        for name in unresolved:
            self.stderr.write(f"  no source photograph for {name}")

    @staticmethod
    def _upload(source):
        content_type = CONTENT_TYPES.get(source.suffix.lower(), "image/jpeg")
        return SimpleUploadedFile(source.name, source.read_bytes(), content_type)

    @staticmethod
    def _sources_complete(missing, photo_dir):
        return all((photo_dir / Path(name).name).exists() for _, _, name in missing)

    @staticmethod
    def _pictures():
        """Every stored picture on the site, as (instance, field name, file)."""
        for post in Post.objects.all():
            if post.image:
                yield post, "image", post.image
        for picture in PostImage.objects.all():
            if picture.image:
                yield picture, "image", picture.image
