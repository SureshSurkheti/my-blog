"""Read the pixel size of images that were uploaded before the fields existed.

Templates emit width/height so the browser can reserve space before an image
loads; without a backfill the existing posts would have no dimensions to emit.
"""

from django.db import migrations
from PIL import Image


def forwards(apps, schema_editor):
    for model_name in ("Post", "PostImage"):
        model = apps.get_model("blog", model_name)
        for instance in model.objects.exclude(image=""):
            if not instance.image:
                continue
            try:
                with Image.open(instance.image.path) as picture:
                    width, height = picture.size
            except (FileNotFoundError, OSError):
                # A missing file shouldn't stop the migration.
                continue
            model.objects.filter(pk=instance.pk).update(
                image_width=width, image_height=height
            )


def backwards(apps, schema_editor):
    """Nothing to undo: 0014 removes the columns."""


class Migration(migrations.Migration):
    dependencies = [("blog", "0014_image_dimensions")]

    operations = [migrations.RunPython(forwards, backwards)]
