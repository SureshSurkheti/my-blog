import markdown as md
import nh3
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from blog.imaging import build_thumbnail, cloudinary_variant

register = template.Library()

# Tags a post body may legitimately use. Anything else is stripped, so a
# post can never inject script into the page.
ALLOWED_TAGS = {
    "p",
    "br",
    "hr",
    "em",
    "strong",
    "del",
    "blockquote",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "dl",
    "dt",
    "dd",
    "a",
    "img",
    "code",
    "pre",
    "span",
    "div",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
}
ALLOWED_ATTRIBUTES = {
    # nh3 adds rel="noopener noreferrer" to links itself.
    "a": {"href", "title"},
    "img": {"src", "alt", "title"},
    "code": {"class"},
    "span": {"class"},
    "div": {"class"},
    "pre": {"class"},
}


@register.filter(name="markdown")
def render_markdown(value):
    """Render Markdown, then sanitize the result before trusting it."""
    if not value:
        return ""
    html = md.markdown(
        value,
        extensions=["extra", "codehilite", "sane_lists", "toc"],
        output_format="html",
    )
    return mark_safe(nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES))


@register.filter
def reading_time(value):
    """Rough minutes-to-read for a body of text, at ~200 words per minute."""
    words = len((value or "").split())
    return max(1, round(words / 200))


@register.simple_tag(takes_context=True)
def query_replace(context, **kwargs):
    """Rebuild the current query string with some params replaced.

    Keeps ``?q=django`` intact while paginating: ``{% query_replace page=2 %}``.
    """
    params = context["request"].GET.copy()
    for key, value in kwargs.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = value
    return params.urlencode()


def stored_width(image):
    """The image's width as recorded in the database, or None.

    ``ImageFieldFile.width`` measures the file, which means opening it. On
    local disk that is cheap; on a remote store it downloads the entire
    original — per image, on every render. The model keeps the width in a
    column (``width_field``) precisely so nothing has to reach for the file to
    lay the page out, and this reads that column.
    """
    field = getattr(image, "field", None)
    column = getattr(field, "width_field", None)
    if not column:
        return None
    return getattr(image.instance, column, None)


@register.simple_tag
def srcset(image):
    """The ``srcset`` for a stored image: every variant, smallest first.

    Cards and gallery tiles are a few hundred pixels wide but the stored file
    is up to 1600px. This offers the browser the whole ladder and lets it pick,
    which is the saving — the markup still names the full-size file in ``src``,
    so a browser that ignores srcset loses nothing.

    The rungs matter as much as their existence. A browser picks the smallest
    candidate that still covers the slot, so a wide gap sends it to the next
    rung up: with only 800 and a 1600 original, a phone at 3x needs ~1085px
    and takes the full-size file. Intermediate widths keep that from happening.

    How the variants are made depends on where the file lives. Locally they are
    generated once and cached on disk. On a remote store nothing here may touch
    the file at all: resizing is handed to the CDN as a URL, because opening
    six originals to measure and shrink them costs more than the request has.

    Returns an empty string when no variant is smaller than the original, so
    the attribute can be omitted rather than naming one file twice.
    """
    if not image:
        return ""

    widths = sorted(settings.IMAGE_UPLOAD["srcset_widths"])
    original = stored_width(image)

    if settings.USE_CLOUDINARY:
        # Every candidate is a plain string built from the delivery URL, so
        # rendering a page makes no network calls of its own.
        if not original:
            # Without the recorded width the only way to know how big the
            # original is would be to fetch it. Not worth a page for.
            return ""
        remote = [
            f"{url} {width}w"
            for width in widths
            if width < original
            and (url := cloudinary_variant(image.url, width)) is not None
        ]
        if not remote:
            return ""
        remote.append(f"{image.url} {original}w")
        return mark_safe(", ".join(remote))

    candidates = []
    for width in widths:
        try:
            variant = build_thumbnail(image.storage, image.name, width=width)
        except (FileNotFoundError, OSError):
            # A missing or unreadable file must not take the page down with it.
            return ""
        if variant:
            candidates.append(f"{image.storage.url(variant)} {width}w")

    if not candidates:
        return ""

    try:
        full = original or image.width
    except (FileNotFoundError, OSError):
        return ""
    candidates.append(f"{image.url} {full}w")
    return mark_safe(", ".join(candidates))
