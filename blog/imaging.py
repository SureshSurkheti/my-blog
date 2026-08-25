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
