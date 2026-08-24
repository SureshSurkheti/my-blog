from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import Author, Comment, Post, PostImage, Tag


def markdown_snippet(image, caption=""):
    """A ready-to-paste Markdown tag for dropping this picture into a post body.

    Body text is Markdown, so an image only needs ``![alt](url)`` — this saves
    hunting for the uploaded file's URL by hand.
    """
    if not image:
        return "—"
    return format_html(
        '<code style="user-select:all;font-size:12px;">![{}]({})</code>',
        caption or "description",
        image.url,
    )


def thumbnail(image, size=60):
    if not image:
        return "—"
    return format_html(
        '<img src="{}" style="height:{}px;width:{}px;object-fit:cover;'
        'border-radius:6px;" />',
        image.url,
        size,
        size,
    )


class PostImageInline(admin.TabularInline):
    """Extra pictures for a post's gallery, uploaded straight from the post."""

    model = PostImage
    extra = 3
    fields = (
        "preview",
        "image",
        "caption",
        "focal_point",
        "sort_order",
        "paste_into_body",
    )
    readonly_fields = ("preview", "paste_into_body")
    ordering = ("sort_order", "id")

    @admin.display(description="Preview")
    def preview(self, obj):
        return thumbnail(obj.image, size=80)

    @admin.display(description="Paste into the body")
    def paste_into_body(self, obj):
        return markdown_snippet(obj.image, obj.caption)


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("user_name", "user_email", "text", "is_approved", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "preview",
        "title",
        "status",
        "published_at",
        "author",
        "gallery_count",
        "comment_count",
    )
    list_display_links = ("preview", "title")
    list_filter = ("status", "author", "tags", "published_at")
    search_fields = ("title", "excerpt", "content")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("author",)
    filter_horizontal = ("tags",)
    date_hierarchy = "published_at"
    readonly_fields = (
        "created_at",
        "updated_at",
        "preview_large",
        "image_markdown",
    )
    inlines = (PostImageInline, CommentInline)
    actions = ("publish_selected", "unpublish_selected")
    fieldsets = (
        (None, {"fields": ("title", "slug", "excerpt")}),
        (
            "Header picture",
            {
                "fields": (
                    "image",
                    "focal_point",
                    "preview_large",
                    "image_markdown",
                ),
                "description": (
                    "Uploads are automatically rotated upright, scaled to at most "
                    "2000px, compressed, and stripped of EXIF metadata (including "
                    "GPS location). Pictures are then scaled to fill their box, "
                    "and whatever overflows is trimmed: the left and right of a "
                    "wide photo, the bottom of a tall one. Focal point picks the "
                    "edge that must survive."
                ),
            },
        ),
        ("Content", {"fields": ("content",)}),
        ("Classification", {"fields": ("author", "tags")}),
        (
            "Publishing",
            {"fields": ("status", "published_at", "created_at", "updated_at")},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("author")
            .annotate(
                _comment_count=Count("comments", distinct=True),
                _gallery_count=Count("gallery", distinct=True),
            )
        )

    @admin.display(description="")
    def preview(self, obj):
        return thumbnail(obj.image)

    @admin.display(description="Current picture")
    def preview_large(self, obj):
        return thumbnail(obj.image, size=200)

    @admin.display(description="Paste into the body")
    def image_markdown(self, obj):
        return markdown_snippet(obj.image, obj.title)

    @admin.display(description="Photos", ordering="_gallery_count")
    def gallery_count(self, obj):
        return obj._gallery_count

    @admin.display(description="Comments", ordering="_comment_count")
    def comment_count(self, obj):
        return obj._comment_count

    @admin.action(description="Publish selected posts")
    def publish_selected(self, request, queryset):
        updated = 0
        for post in queryset:
            post.status = Post.Status.PUBLISHED
            post.save()  # keeps the published_at stamping logic in one place
            updated += 1
        self.message_user(request, f"{updated} post(s) published.")

    @admin.action(description="Move selected posts back to draft")
    def unpublish_selected(self, request, queryset):
        updated = queryset.update(status=Post.Status.DRAFT)
        self.message_user(request, f"{updated} post(s) moved to draft.")


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ("preview", "post", "caption", "sort_order", "paste_into_body")
    list_display_links = ("preview", "caption")
    list_filter = ("post",)
    list_editable = ("sort_order",)
    autocomplete_fields = ("post",)

    @admin.display(description="")
    def preview(self, obj):
        return thumbnail(obj.image, size=80)

    @admin.display(description="Paste into the body")
    def paste_into_body(self, obj):
        return markdown_snippet(obj.image, obj.caption)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email_address", "post_count")
    search_fields = ("first_name", "last_name", "email_address")
    prepopulated_fields = {"slug": ("first_name", "last_name")}

    @admin.display(description="Posts")
    def post_count(self, obj):
        return obj.posts.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("caption", "slug", "post_count")
    search_fields = ("caption",)
    prepopulated_fields = {"slug": ("caption",)}

    @admin.display(description="Posts")
    def post_count(self, obj):
        return obj.posts.count()


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user_name", "post", "is_approved", "created_at", "short_text")
    list_filter = ("is_approved", "created_at", "post")
    search_fields = ("user_name", "user_email", "text")
    readonly_fields = ("created_at",)
    actions = ("approve_selected", "unapprove_selected")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("post")

    @admin.display(description="Comment")
    def short_text(self, obj):
        return obj.text[:60] + ("..." if len(obj.text) > 60 else "")

    @admin.action(description="Approve selected comments")
    def approve_selected(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} comment(s) approved and now visible.")

    @admin.action(description="Hide selected comments")
    def unapprove_selected(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} comment(s) hidden.")
