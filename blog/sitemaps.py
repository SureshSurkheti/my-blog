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
        return Post.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


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
