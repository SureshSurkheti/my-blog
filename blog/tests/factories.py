"""Small helpers so each test only spells out the fields it cares about."""

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from blog.models import Author, Comment, Post, PostImage, Tag


def make_author(first_name="Ada", last_name="Lovelace", **kwargs):
    return Author.objects.create(
        first_name=first_name,
        last_name=last_name,
        email_address=kwargs.pop("email_address", "ada@example.com"),
        **kwargs,
    )


def make_tag(caption="Django", **kwargs):
    return Tag.objects.create(caption=caption, **kwargs)


def make_post(title="A Post", published=True, **kwargs):
    kwargs.setdefault("slug", title.lower().replace(" ", "-"))
    kwargs.setdefault("excerpt", "A short summary.")
    kwargs.setdefault("content", "Body text that is comfortably long enough.")
    kwargs.setdefault("author", None)
    tags = kwargs.pop("tags", [])

    post = Post.objects.create(
        title=title,
        status=Post.Status.PUBLISHED if published else Post.Status.DRAFT,
        **kwargs,
    )
    if tags:
        post.tags.set(tags)
    return post


def make_future_post(title="Scheduled", **kwargs):
    """A post marked published but dated ahead, i.e. not yet visible."""
    return make_post(
        title=title,
        published=True,
        published_at=timezone.now() + timezone.timedelta(days=3),
        **kwargs,
    )


def make_comment(post, user_name="Grace", approved=True, **kwargs):
    return Comment.objects.create(
        post=post,
        user_name=user_name,
        user_email=kwargs.pop("user_email", "grace@example.com"),
        text=kwargs.pop("text", "Nice write-up, thanks!"),
        is_approved=approved,
        **kwargs,
    )


def make_gallery_image(post, caption="A street in Beppu", **kwargs):
    return PostImage.objects.create(
        post=post,
        image=kwargs.pop("image", make_image_file("gallery.jpg")),
        caption=caption,
        **kwargs,
    )


def make_image_file(
    name="photo.jpg", size=(1200, 800), color=(90, 20, 160), fmt="JPEG"
):
    """An in-memory uploaded image, for testing the upload pipeline."""
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, format=fmt)
    return SimpleUploadedFile(
        name, buffer.getvalue(), content_type=f"image/{fmt.lower()}"
    )
