"""Move existing pictures off "Center" so their tops stop being trimmed.

The focal point defaulted to Center when the field was introduced, which crops
a tall photo evenly top and bottom. Nothing had been set deliberately yet, so
every Center row becomes Top; anything explicitly set to another side is left
alone.
"""

from django.db import migrations


def forwards(apps, schema_editor):
    for model_name in ("Post", "PostImage"):
        model = apps.get_model("blog", model_name)
        model.objects.filter(focal_point="center").update(focal_point="top")


def backwards(apps, schema_editor):
    for model_name in ("Post", "PostImage"):
        model = apps.get_model("blog", model_name)
        model.objects.filter(focal_point="top").update(focal_point="center")


class Migration(migrations.Migration):
    dependencies = [("blog", "0011_default_focal_point_top")]

    operations = [migrations.RunPython(forwards, backwards)]
