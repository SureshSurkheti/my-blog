"""Per-page SEO metadata.

Views build one ``seo`` dict; ``templates/includes/seo.html`` renders it into
canonical, Open Graph, Twitter and JSON-LD tags. Keeping it in Python rather
than template blocks means the same title can feed <title>, og:title and the
structured data without being written three times — and it can be tested.
"""

import json

from django.conf import settings
from django.templatetags.static import static


def absolute(request, path):
    """Turn a root-relative path into the full URL crawlers need."""
    return request.build_absolute_uri(path)


def canonical(request):
    """The page's own address, keeping only parameters that change content.

    Pagination genuinely produces different pages, so ``?page=`` is kept.
    Anything else (campaign tags, stray parameters) is dropped so the same
    content is not indexed under many URLs.
    """
    url = request.build_absolute_uri(request.path)
    page = request.GET.get("page")
    return f"{url}?page={page}" if page and page != "1" else url


def build(
    request,
    *,
    title=None,
    description=None,
    image=None,
    og_type="website",
    published=None,
    modified=None,
    author=None,
    tags=(),
    noindex=False,
    json_ld=None,
):
    blog = settings.BLOG_SETTINGS
    title = title or blog["title"]
    description = description or blog["description"]
    image_url = absolute(request, image or static("icon-512.png"))

    data = {
        "title": title,
        "description": description,
        "canonical": canonical(request),
        "image": image_url,
        "og_type": og_type,
        "site_name": blog["title"],
        "published": published,
        "modified": modified,
        "author": author,
        "tags": list(tags),
        "noindex": noindex,
    }
    data["json_ld"] = _dump(json_ld) if json_ld else None
    return data


def _dump(payload):
    """JSON for a <script> block, with `<` escaped so it can't break out."""
    return json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")


def author_schema():
    """The person behind the site, as one entity with every profile attached.

    ``sameAs`` is how a search engine learns that this blog, the portfolio at
    the author's own domain and the social profiles are one person rather than
    several who share a name. Without it each is judged on its own; with it the
    reputation of all of them is pooled. Returns None if nothing is configured
    beyond a bare name, since a Person with no identifiers asserts nothing.
    """
    author = settings.AUTHOR_SITE
    profiles = [link["url"] for link in settings.SOCIAL_LINKS]
    if author["url"] and author["url"] not in profiles:
        profiles.insert(0, author["url"])
    if not profiles:
        return None

    schema = {"@type": "Person", "name": author["name"], "sameAs": profiles}
    if author["url"]:
        schema["url"] = author["url"]
    return schema


def website_schema(request):
    """Site-level schema, including the search box Google may surface."""
    blog = settings.BLOG_SETTINGS
    home = absolute(request, "/")
    author = author_schema()
    schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": blog["title"],
        "description": blog["description"],
        "url": home,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{home}search?q={{search_term_string}}",
            },
            "query-input": "required name=search_term_string",
        },
    }
    if author:
        schema["author"] = author
    return schema


def post_schema(request, post):
    """BlogPosting schema — what earns a rich result for an article."""
    image = post.image.url if post.image else static("icon-512.png")
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.title,
        "description": post.excerpt,
        "image": [absolute(request, image)],
        "url": absolute(request, post.get_absolute_url()),
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": absolute(request, post.get_absolute_url()),
        },
        "datePublished": post.published_at.isoformat() if post.published_at else None,
        "dateModified": post.updated_at.isoformat(),
        "keywords": [tag.caption for tag in post.tags.all()],
        "publisher": {
            "@type": "Organization",
            "name": settings.BLOG_SETTINGS["title"],
            "logo": {
                "@type": "ImageObject",
                "url": absolute(request, static("icon-512.png")),
            },
        },
    }
    if post.author:
        author = {
            "@type": "Person",
            "name": post.author.full_name,
            "url": absolute(request, post.author.get_absolute_url()),
        }
        # Only the site owner gets the external profiles attached. A guest
        # author shares the byline, not the identity, and claiming otherwise
        # would tell search engines something untrue.
        if post.author.full_name == settings.AUTHOR_SITE["name"]:
            identity = author_schema()
            if identity:
                author["sameAs"] = identity["sameAs"]
        schema["author"] = author
    return {key: value for key, value in schema.items() if value is not None}


def breadcrumbs(request, trail):
    """trail: [(name, path), ...] ending at the current page."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "name": name,
                "item": absolute(request, path),
            }
            for index, (name, path) in enumerate(trail, start=1)
        ],
    }
