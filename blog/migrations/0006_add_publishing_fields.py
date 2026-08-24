"""Add slugs, publishing state and timestamps as nullable columns.

Split into three migrations so existing rows can be backfilled (0007) before
the constraints are tightened (0008).
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("blog", "0005_comment")]

    operations = [
        migrations.AddField(
            model_name="tag",
            name="slug",
            field=models.SlugField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="author",
            name="slug",
            field=models.SlugField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="author",
            name="bio",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="post",
            name="status",
            field=models.CharField(default="draft", max_length=10),
        ),
        migrations.AddField(
            model_name="post",
            name="published_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="post",
            name="created_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="post",
            name="updated_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="comment",
            name="created_at",
            field=models.DateTimeField(null=True),
        ),
    ]
