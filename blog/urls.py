from django.urls import path

from . import views
from .feeds import LatestPostsAtomFeed, LatestPostsFeed

urlpatterns = [
    path("", views.StartingPageView.as_view(), name="starting-page"),
    path("posts", views.AllPostsView.as_view(), name="posts-page"),
    path("posts/<slug:slug>", views.SinglePostView.as_view(), name="post-detail-page"),
    path("tags/<slug:slug>", views.TagPostsView.as_view(), name="tag-posts-page"),
    path(
        "authors/<slug:slug>",
        views.AuthorPostsView.as_view(),
        name="author-posts-page",
    ),
    path("search", views.SearchView.as_view(), name="search-page"),
    path("read-later", views.ReadLaterView.as_view(), name="read-later"),
    path("feed/rss", LatestPostsFeed(), name="post-feed-rss"),
    path("feed/atom", LatestPostsAtomFeed(), name="post-feed-atom"),
]
