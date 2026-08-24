"""Tighten the backfilled columns to their final shape and drop `date`.

`date` used auto_now=True, so it tracked the last edit rather than publication;
0007 copied its value into published_at/created_at before it goes away here.
"""

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("blog", "0007_backfill_publishing_data")]

    operations = [
        migrations.RemoveField(model_name="post", name="date"),
        migrations.AlterField(
            model_name="tag",
            name="caption",
            field=models.CharField(max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name="tag",
            name="slug",
            field=models.SlugField(blank=True, max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="author",
            name="slug",
            field=models.SlugField(blank=True, max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="author",
            name="bio",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="post",
            name="slug",
            field=models.SlugField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="post",
            name="status",
            field=models.CharField(
                choices=[("draft", "Draft"), ("published", "Published")],
                db_index=True,
                default="draft",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="published_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Set automatically the first time the post is published.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="post",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="post",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="posts"),
        ),
        migrations.AlterField(
            model_name="post",
            name="content",
            field=models.TextField(
                help_text="Markdown is supported.",
                validators=[django.core.validators.MinLengthValidator(10)],
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="tags",
            field=models.ManyToManyField(
                blank=True, related_name="posts", to="blog.tag"
            ),
        ),
        migrations.AlterField(
            model_name="comment",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterModelOptions(
            name="tag",
            options={"ordering": ["caption"]},
        ),
        migrations.AlterModelOptions(
            name="author",
            options={"ordering": ["last_name", "first_name"]},
        ),
        migrations.AlterModelOptions(
            name="post",
            options={"ordering": ["-published_at", "-created_at"]},
        ),
        migrations.AlterModelOptions(
            name="comment",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="post",
            index=models.Index(
                fields=["-published_at"], name="blog_post_publish_2c9212_idx"
            ),
        ),
    ]
