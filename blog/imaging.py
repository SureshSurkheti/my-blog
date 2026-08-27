"""Upload-time image processing.

Photos straight off a phone or camera are typically several megabytes and
carry EXIF metadata — including GPS coordinates, which matters for a travel
blog. Every uploaded image is therefore re-encoded on save: rotated upright,
scaled down to a sane maximum, compressed, and stripped of metadata.
"""

from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, ImageOps


def _has_transparency(image):
    if image.mode in ("RGBA", "LA"):
        alpha = image.getchannel("A")
        return alpha.getextrema()[0] < 255
    return image.mode == "P" and "transparency" in image.info


def optimize_uploaded_image(field_file, max_dimension=None, quality=None):
    """Re-encode a freshly uploaded image in place.

    Returns ``(width, height)`` of the stored image when it was processed, or
    False when there was nothing to do — files already stored (any save that
    didn't come with a new upload) are left untouched, so editing a post's
    title never re-compresses its picture.

    The size is returned because re-saving through ``FieldFile.save()`` makes
    Django clear the model's width/height fields; the caller writes the real
    values back from here rather than letting Django re-open the file.
    """
    if not field_file:
        return False

    if max_dimension is None:
        max_dimension = settings.IMAGE_UPLOAD["max_dimension"]
    if quality is None:
        quality = settings.IMAGE_UPLOAD["jpeg_quality"]

    uploaded = getattr(field_file, "file", None)
    if not isinstance(uploaded, UploadedFile):
        return False

    uploaded.seek(0)
    with Image.open(uploaded) as opened:
        # Honour the camera's rotation flag, then drop the EXIF block entirely.
        image = ImageOps.exif_transpose(opened)
        keep_alpha = _has_transparency(image)

        if keep_alpha:
            image = image.convert("RGBA")
            fmt, suffix = "PNG", ".png"
            save_kwargs = {"optimize": True}
        else:
            image = image.convert("RGB")
            fmt, suffix = "JPEG", ".jpg"
            save_kwargs = {"optimize": True, "quality": quality, "progressive": True}

        image.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

        buffer = BytesIO()
        image.save(buffer, format=fmt, **save_kwargs)

    width, height = image.size
    name = Path(field_file.name).with_suffix(suffix).name
    field_file.save(name, ContentFile(buffer.getvalue()), save=False)
    return width, height


def thumbnail_name(name, width):
    """Where the narrow variant of ``name`` lives, e.g. beppu.jpg -> beppu.800w.jpg."""
    path = Path(name)
    return str(path.with_suffix(f".{width}w{path.suffix}"))


def build_thumbnail(storage, name, width=None, quality=None):
    """Write a narrower copy of a stored image beside it, once.

    Cards and gallery tiles are a few hundred pixels wide, but the stored file
    is up to 1600px — roughly twenty times the data a card actually needs.
    Returns the thumbnail's storage name, or None if the source is already
    narrow enough to be worth serving as-is.
    """
    if width is None:
        width = settings.IMAGE_UPLOAD["thumbnail_width"]
    if quality is None:
        quality = settings.IMAGE_UPLOAD["jpeg_quality"]

    target = thumbnail_name(name, width)
    if storage.exists(target):
        return target

    with storage.open(name, "rb") as handle:
        with Image.open(handle) as opened:
            if opened.width <= width:
                return None
            image = opened.convert("RGB")
            image.thumbnail((width, width * 10), Image.LANCZOS)
            buffer = BytesIO()
            image.save(
                buffer,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )

    storage.save(target, ContentFile(buffer.getvalue()))
    return target


# Cloudinary delivery URLs carry their transformations as a path segment right
# after "/image/upload/", so a variant is a string edit rather than a request.
CLOUDINARY_UPLOAD_MARKER = "/image/upload/"


def cloudinary_variant(url, width):
    """A resized delivery URL for an image already hosted on Cloudinary.

    Cloudinary resizes at its own edge, so the variant costs nothing to make:
    no download, no re-encode, no upload, and no API call from us. That is the
    whole point of using it here. Generating thumbnails ourselves against a
    remote storage means a round trip per width per image on every render —
    six images at three widths is eighteen sequential HTTP calls, which is
    slower than the worker timeout and takes the page down with it.

    ``c_limit`` only ever shrinks, so an image narrower than ``width`` is left
    alone rather than being blown up. ``q_auto,f_auto`` let Cloudinary pick the
    quality and hand WebP or AVIF to browsers that accept them.

    Returns None if the URL is not a Cloudinary delivery URL, so the caller can
    fall back rather than emit something broken.
    """
    if CLOUDINARY_UPLOAD_MARKER not in url:
        return None
    head, tail = url.split(CLOUDINARY_UPLOAD_MARKER, 1)
    return f"{head}{CLOUDINARY_UPLOAD_MARKER}w_{width},c_limit,q_auto,f_auto/{tail}"
