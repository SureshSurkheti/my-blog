from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import ListView

from . import credits, seo
from .forms import CommentForm
from .models import Author, Post, Tag

SESSION_KEY = "stored_posts"


def _stored_post_ids(request):
    """Read-later ids held in the session, always as a list of ints."""
    stored = request.session.get(SESSION_KEY) or []
    return [int(pk) for pk in stored]


class PublishedPostListView(ListView):
    """Base list view: published posts only, paginated, related data prefetched."""

    model = Post
    context_object_name = "posts"

    def get_paginate_by(self, queryset):
        return settings.BLOG_SETTINGS["posts_per_page"]

    def get_queryset(self):
        return Post.objects.published().with_related()


class StartingPageView(PublishedPostListView):
    template_name = "blog/index.html"
    paginate_by = None

    def get_paginate_by(self, queryset):
        return None

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            # The card list is capped at latest_posts_count, so the archive
            # total has to be counted separately for the hero.
            total_posts=Post.objects.published().count(),
            seo=seo.build(self.request, json_ld=seo.website_schema(self.request)),
            **kwargs,
        )

    def get_queryset(self):
        limit = settings.BLOG_SETTINGS["latest_posts_count"]
        return super().get_queryset()[:limit]


class AllPostsView(PublishedPostListView):
    template_name = "blog/all-posts.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            seo=seo.build(
                self.request,
                title=f"All posts · {settings.BLOG_SETTINGS['title']}",
                description="Every post on the blog, newest first.",
            ),
            **kwargs,
        )


class TagPostsView(PublishedPostListView):
    template_name = "blog/tag-posts.html"

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs["slug"])
        return super().get_queryset().filter(tags=self.tag)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            tag=self.tag,
            seo=seo.build(
                self.request,
                title=f"Posts tagged “{self.tag.caption}”",
                description=f"Every post tagged {self.tag.caption}.",
            ),
            **kwargs,
        )


class AuthorPostsView(PublishedPostListView):
    template_name = "blog/author-posts.html"

    def get_queryset(self):
        self.author = get_object_or_404(Author, slug=self.kwargs["slug"])
        return super().get_queryset().filter(author=self.author)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            author=self.author,
            seo=seo.build(
                self.request,
                title=f"Posts by {self.author.full_name}",
                description=self.author.bio
                or f"Every post written by {self.author.full_name}.",
            ),
            **kwargs,
        )


class SearchView(PublishedPostListView):
    template_name = "blog/search.html"

    def get_queryset(self):
        self.query = self.request.GET.get("q", "").strip()
        if not self.query:
            return Post.objects.none()
        return super().get_queryset().search(self.query)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            query=self.query,
            seo=seo.build(
                self.request,
                title=f"Search: {self.query}" if self.query else "Search",
                description="Search the archive.",
                # Search results are thin and endless; useful to follow,
                # not worth indexing.
                noindex=True,
            ),
            **kwargs,
        )


class PhotoCreditsView(View):
    """Attribution for the photographs that are not the owner's own work."""

    template_name = "blog/credits.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "groups": credits.grouped(),
                "seo": seo.build(
                    request,
                    title="Photo credits",
                    description=(
                        "Photographers and licences for the pictures used on this blog."
                    ),
                    # A credit list is for readers and for the licences, not
                    # something search engines need in their index.
                    noindex=True,
                ),
            },
        )


class SinglePostView(View):
    template_name = "blog/post-detail.html"

    def get_post(self, slug):
        # Staff may preview drafts; everybody else only sees published posts.
        queryset = Post.objects.with_related().prefetch_related("gallery")
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.published()
        return get_object_or_404(queryset, slug=slug)

    def build_context(self, request, post, comment_form=None):
        return {
            "post": post,
            "post_tags": post.tags.all(),
            "gallery": post.gallery.all(),
            "comment_form": comment_form or CommentForm(),
            "comments": post.comments.approved(),
            "saved_for_later": post.id in _stored_post_ids(request),
            "newer_post": post.get_newer_post(),
            "older_post": post.get_older_post(),
            "seo": seo.build(
                request,
                title=post.title,
                description=post.excerpt,
                image=post.image.url if post.image else None,
                og_type="article",
                published=post.published_at,
                modified=post.updated_at,
                author=post.author.full_name if post.author else None,
                tags=[tag.caption for tag in post.tags.all()],
                noindex=not post.is_published,
                # A list, so the post and its breadcrumb trail both ship.
                # Breadcrumbs are what Google renders in place of the raw URL
                # under a search result.
                json_ld=[
                    seo.post_schema(request, post),
                    seo.breadcrumbs(
                        request,
                        [
                            ("Home", reverse("starting-page")),
                            ("All posts", reverse("posts-page")),
                            (post.title, post.get_absolute_url()),
                        ],
                    ),
                ],
            ),
        }

    def get(self, request, slug):
        post = self.get_post(slug)
        return render(request, self.template_name, self.build_context(request, post))

    def post(self, request, slug):
        post = self.get_post(slug)
        comment_form = CommentForm(request.POST)

        if comment_form.is_spam:
            # Silently accept and drop it: telling a bot it failed just invites
            # a retry, and a human can never trip this.
            return HttpResponseRedirect(post.get_absolute_url())

        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.save()
            messages.success(
                request,
                "Thanks! Your comment has been sent and will appear once approved.",
            )
            return HttpResponseRedirect(post.get_absolute_url())

        context = self.build_context(request, post, comment_form=comment_form)
        return render(request, self.template_name, context, status=400)


class ReadLaterView(View):
    """Session-backed reading list. POST toggles a post in or out of the list."""

    template_name = "blog/stored-posts.html"

    def get(self, request):
        stored = _stored_post_ids(request)
        posts = (
            Post.objects.published().with_related().filter(id__in=stored)
            if stored
            else Post.objects.none()
        )
        context = {
            "posts": posts,
            "has_posts": bool(posts),
            "seo": seo.build(
                request,
                title="Saved",
                description="Posts you have saved to read later.",
                # Private to one visitor's session — nothing to index.
                noindex=True,
            ),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            post_id = int(request.POST["post_id"])
        except (KeyError, ValueError):
            return HttpResponseRedirect(reverse("read-later"))

        stored = _stored_post_ids(request)
        if post_id in stored:
            stored.remove(post_id)
            messages.info(request, "Removed from your saved posts.")
        else:
            stored.append(post_id)
            messages.success(request, "Saved for later.")

        request.session[SESSION_KEY] = stored
        return HttpResponseRedirect(self.redirect_target(request))

    def redirect_target(self, request):
        target = request.POST.get("next") or ""
        if target and url_has_allowed_host_and_scheme(
            target,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return target
        return reverse("read-later")
