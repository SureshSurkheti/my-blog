from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Author, Post, Tag


class StaticViewSitemap(Sitemap):
    """The pages that aren't generated from a model."""

    changefreq = "daily"
    priority = 1.0

    def items(self):
        return ["starting-page", "posts-page"]

    def location(self, item):
        return reverse(item)


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Post.objects.published().prefetch_related("gallery")

    def lastmod(self, obj):
        return obj.updated_at

    def _urls(self, page, protocol, domain):
        """Attach each post's photographs to its entry in the sitemap.

        Google finds images it would otherwise miss through an image sitemap,
        and for travel writing the photographs are a large part of what people
        are searching for. Without this the sitemap names the page and says
        nothing about the dozen pictures on it.

        ``_urls`` is Django's own method rather than a documented hook, because
        a Sitemap has no public way to add fields to a single entry. It is
        covered by tests that fail loudly if the shape it returns ever changes.
        """
        urls = super()._urls(page, protocol, domain)
        for url in urls:
            url["images"] = sitemap_images(url["item"], protocol, domain)
        return urls


def sitemap_images(post, protocol, domain):
    """Every picture on a post, as absolute URLs with a caption each.

    Cloudinary already hands back absolute URLs; the local filesystem does
    not, so a relative one is completed here. A caption is what Google shows
    beside the image, so the post's title stands in for the header picture,
    which has no caption of its own.
    """
    pictures = []
    if post.image:
        pictures.append((post.image, post.title))
    pictures.extend((item.image, item.caption or post.title) for item in post.gallery.all())

    entries = []
    for image, caption in pictures:
        if not image:
            continue
        location = image.url
        if location.startswith("/"):
            location = f"{protocol}://{domain}{location}"
        entries.append({"loc": location, "caption": caption})
    return entries


class TagSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.4

    def items(self):
        # A tag carried only by drafts renders a page with nothing on it.
        # Listing that is worse than not listing it at all, so a tag waits
        # here until one of its posts is actually published.
        return Tag.objects.filter(posts__in=Post.objects.published()).distinct()


class AuthorSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.4

    def items(self):
        # Same reasoning as the tags: an author with nothing published yet
        # has an empty page, and an empty page should not be advertised.
        return Author.objects.filter(posts__in=Post.objects.published()).distinct()
