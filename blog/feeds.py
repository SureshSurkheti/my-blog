from django.conf import settings
from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.feedgenerator import Atom1Feed

from .models import Post


class LatestPostsFeed(Feed):
    @property
    def title(self):
        return settings.BLOG_SETTINGS["title"]

    @property
    def description(self):
        return settings.BLOG_SETTINGS["description"]

    def link(self):
        return reverse("starting-page")

    def items(self):
        return Post.objects.published().with_related()[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_pubdate(self, item):
        return item.published_at

    def item_author_name(self, item):
        return item.author.full_name if item.author else None

    def item_link(self, item):
        return item.get_absolute_url()


class LatestPostsAtomFeed(LatestPostsFeed):
    feed_type = Atom1Feed
    subtitle = LatestPostsFeed.description
