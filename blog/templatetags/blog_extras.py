import markdown as md
import nh3
from django import template
from django.utils.safestring import mark_safe

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
