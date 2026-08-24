"""Approve the comments that predate moderation.

They were already publicly visible, so leaving them unapproved would silently
delete them from the site.
"""

from django.db import migrations


def forwards(apps, schema_editor):
    Comment = apps.get_model("blog", "Comment")
    Comment.objects.update(is_approved=True)


def backwards(apps, schema_editor):
    """Nothing to undo: 0009 drops the column."""


class Migration(migrations.Migration):
    dependencies = [("blog", "0009_gallery_and_moderation")]

    operations = [migrations.RunPython(forwards, backwards)]
