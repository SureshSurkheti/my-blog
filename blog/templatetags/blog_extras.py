import markdown as md
import nh3
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from blog.imaging import build_thumbnail

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


@register.simple_tag
def srcset(image):
    """A two-entry ``srcset`` for a stored image, small variant first.

    Cards and gallery tiles are a few hundred pixels wide but the stored file
    is up to 1600px. This offers the browser both and lets it pick, which is
    the whole saving — the markup still names the full-size file in ``src``,
    so a browser that ignores srcset loses nothing.

    Returns an empty string when there is no smaller variant to offer, so the
    attribute can be omitted entirely rather than repeating one file twice.
    """
    if not image:
        return ""
    try:
        thumb = build_thumbnail(image.storage, image.name)
    except (FileNotFoundError, OSError):
        # A missing or unreadable file must not take the page down with it.
        return ""
    if not thumb:
        return ""

    width = settings.IMAGE_UPLOAD["thumbnail_width"]
    return mark_safe(f"{image.storage.url(thumb)} {width}w, {image.url} {image.width}w")
