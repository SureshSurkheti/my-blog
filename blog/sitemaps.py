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
        return Tag.objects.all()


class AuthorSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.4

    def items(self):
        return Author.objects.all()
