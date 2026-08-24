"""Backfill the columns added in 0006 from the pre-existing data.

Every post that existed before this upgrade was live on the site, so each one
is marked published and keeps its original ``date`` as the publish date.
"""

from datetime import datetime, time

from django.db import migrations
from django.utils import timezone
from django.utils.text import slugify


def unique_slug(model, base, taken):
    base = slugify(base)[:90] or "item"
    slug = base
    counter = 2
    while slug in taken:
        slug = f"{base}-{counter}"
        counter += 1
    taken.add(slug)
    return slug


def forwards(apps, schema_editor):
    Tag = apps.get_model("blog", "Tag")
    Author = apps.get_model("blog", "Author")
    Post = apps.get_model("blog", "Post")
    Comment = apps.get_model("blog", "Comment")

    taken = set()
    for tag in Tag.objects.all():
        tag.slug = unique_slug(Tag, tag.caption, taken)
        tag.save(update_fields=["slug"])

    taken = set()
    for author in Author.objects.all():
        name = f"{author.first_name} {author.last_name}".strip()
        author.slug = unique_slug(Author, name, taken)
        author.save(update_fields=["slug"])

    now = timezone.now()
    for post in Post.objects.all():
        # `date` was a DateField; anchor it at midday so rendering in any
        # timezone keeps the original calendar day.
        stamp = timezone.make_aware(datetime.combine(post.date, time(12, 0)))
        post.status = "published"
        post.published_at = stamp
        post.created_at = stamp
        post.updated_at = stamp
        post.save(update_fields=["status", "published_at", "created_at", "updated_at"])

    Comment.objects.filter(created_at__isnull=True).update(created_at=now)


def backwards(apps, schema_editor):
    """Nothing to undo: 0006 removes the columns this filled in."""


class Migration(migrations.Migration):
    dependencies = [("blog", "0006_add_publishing_fields")]

    operations = [migrations.RunPython(forwards, backwards)]
