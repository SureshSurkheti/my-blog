from django.contrib.sitemaps import Sitemap

from .models import Author, Post, Tag


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
