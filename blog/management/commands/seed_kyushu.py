"""Replace the blog's contents with the twelve Kyushu travel posts.

Run ``fetch_seed_photos`` first — this command only reads what that put on
disk, so it needs no network and can be re-run safely.

Deleting posts also deletes their comments and gallery images, so the command
refuses to touch anything without an explicit ``--replace``, and it never
removes files from MEDIA_ROOT that other posts might still point at.
"""

import json
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from blog import credits as photo_credits
from blog.models import Author, Post, PostImage, Tag
from blog.seed_data import AUTHOR, POSTS


class Command(BaseCommand):
    help = "Load the Kyushu travel posts, optionally replacing existing ones."

    def add_arguments(self, parser):
        parser.add_argument(
            "--photos",
            default="seed_photos",
            help="Directory holding the downloaded photos and credits.json.",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete every existing post (and its comments) first.",
        )

    def handle(self, *args, **options):
        photo_dir = Path(options["photos"])
        credits = self._load_credits(photo_dir)

        with transaction.atomic():
            if options["replace"]:
                deleted, _ = Post.objects.all().delete()
                self.stdout.write(f"Deleted {deleted} existing rows (posts + related).")

            author = self._author()
            attributions = {}
            for spec in POSTS:
                self._create_post(spec, author, photo_dir, credits, attributions)

            # A --replace leaves the old posts' tags behind pointing at
            # nothing; an empty tag page is a dead end for readers and
            # crawlers alike.
            orphans = Tag.objects.filter(posts__isnull=True)
            if orphans:
                self.stdout.write(
                    f"Removed {orphans.count()} tag(s) with no posts: "
                    + ", ".join(sorted(t.caption for t in orphans))
                )
                orphans.delete()

        self._write_attributions(attributions)
        self.stdout.write(
            self.style.SUCCESS(f"{Post.objects.published().count()} published posts.")
        )

    # -- pieces -----------------------------------------------------------

    def _load_credits(self, photo_dir):
        path = photo_dir / "credits.json"
        if not path.exists():
            raise CommandError(
                f"No credits.json in {photo_dir}/. "
                "Run `manage.py fetch_seed_photos` first."
            )
        return json.loads(path.read_text())

    def _author(self):
        author, _ = Author.objects.update_or_create(
            email_address=AUTHOR["email_address"],
            defaults={k: v for k, v in AUTHOR.items() if k != "email_address"},
        )
        return author

    def _create_post(self, spec, author, photo_dir, credits, attributions):
        published_at = timezone.make_aware(
            datetime.strptime(spec["published"], "%Y-%m-%d %H:%M")
        )

        post = Post(
            title=spec["title"],
            slug=spec["slug"],
            excerpt=spec["excerpt"],
            content=spec["content"],
            author=author,
            focal_point=spec["focal_point"],
            status=Post.Status.PUBLISHED,
            published_at=published_at,
        )
        self._attach(post, "image", photo_dir, credits, spec["image"])
        post.save()
        post.tags.set(self._tags(spec["tags"]))
        self._record(attributions, post, post.image.name, credits[spec["image"]])

        for order, entry in enumerate(spec["gallery"]):
            # A gallery entry may carry its own focal point as a third item;
            # the post's own setting is only a default. The gallery crops to a
            # wide letterbox, so a picture whose subject sits high in the frame
            # needs "top" even when the post's header wants "center".
            name, caption, *rest = entry
            picture = PostImage(
                post=post,
                caption=caption,
                sort_order=order,
                focal_point=rest[0] if rest else spec["focal_point"],
            )
            self._attach(picture, "image", photo_dir, credits, name)
            picture.save()
            self._record(attributions, post, picture.image.name, credits[name])

        self.stdout.write(f"  {post.slug} (+{len(spec['gallery'])} gallery)")

    def _attach(self, instance, field, photo_dir, credits, commons_title):
        entry = credits.get(commons_title)
        if entry is None:
            raise CommandError(f"{commons_title!r} is missing from credits.json")
        path = photo_dir / entry["file"]
        if not path.exists():
            raise CommandError(f"{path} is listed in credits.json but not on disk")
        # SimpleUploadedFile, not a plain File: optimize_uploaded_image only
        # processes genuine uploads, so a plain File would store the original
        # at full size and skip the resize entirely.
        upload = SimpleUploadedFile(
            entry["file"], path.read_bytes(), content_type="image/jpeg"
        )
        setattr(instance, field, upload)

    def _tags(self, captions):
        tags = []
        for caption in captions:
            tag, _ = Tag.objects.get_or_create(caption=caption)
            tags.append(tag)
        return tags

    @staticmethod
    def _record(attributions, post, stored_name, entry):
        """Note who took one stored picture, keyed by the file on disk.

        Attribution lives here rather than in the post body: CC BY and CC BY-SA
        require credit, but a credit list under every article is noise for a
        reader. The credits page renders this file instead.
        """
        attributions[stored_name] = {
            "post": post.title,
            "post_url": post.get_absolute_url(),
            "artist": entry["artist"],
            "licence": entry["licence"],
            "licence_url": entry["licence_url"],
            "source": entry["source"],
        }

    def _write_attributions(self, attributions):
        # Resolved through the module, not bound at import, so a test can
        # redirect it — otherwise running the suite overwrites the real file.
        path = photo_credits.ATTRIBUTIONS_PATH
        shown = (
            path.relative_to(settings.BASE_DIR)
            if path.is_relative_to(settings.BASE_DIR)
            else path
        )
        path.write_text(
            json.dumps(attributions, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n"
        )
        self.stdout.write(f"Wrote {len(attributions)} photo credits to {shown}")
