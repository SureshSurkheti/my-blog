from django.core.validators import MinLengthValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .imaging import optimize_uploaded_image


class FocalPoint(models.TextChoices):
    """Which edge of a picture must survive when a layout has to crop it.

    Pictures are scaled to fill a fixed box, so whichever dimension overflows
    gets trimmed — the sides on a wide photo, the top and/or bottom on a tall
    one. This setting says which edge is protected; the trimming is then taken
    from the others as needed. The templates turn it into a CSS
    ``object-position``.
    """

    CENTER = "center", "Centre — trim every side evenly"
    TOP = "top", "Keep the top — trim the sides and the bottom"
    BOTTOM = "bottom", "Keep the bottom — trim the sides and the top"
    LEFT = "left", "Keep the left — trim the right, top and bottom"
    RIGHT = "right", "Keep the right — trim the left, top and bottom"

    @classmethod
    def to_css(cls, value):
        return {
            cls.CENTER: "50% 50%",
            cls.TOP: "50% 0%",
            cls.BOTTOM: "50% 100%",
            cls.LEFT: "0% 50%",
            cls.RIGHT: "100% 50%",
        }.get(value, "50% 50%")


class SluggedModel(models.Model):
    """Shared slug behaviour: derive the slug from a source field when blank."""

    slug = models.SlugField(unique=True, blank=True, max_length=100)

    slug_source_field = None

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug(getattr(self, self.slug_source_field))
        super().save(*args, **kwargs)

    def _unique_slug(self, value):
        base = slugify(value)[:90] or "item"
        slug = base
        counter = 2
        existing = type(self).objects.exclude(pk=self.pk)
        while existing.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug


class Tag(SluggedModel):
    caption = models.CharField(max_length=20, unique=True)

    slug_source_field = "caption"

    class Meta:
        ordering = ["caption"]

    def __str__(self):
        return self.caption

    def get_absolute_url(self):
        return reverse("tag-posts-page", args=[self.slug])


class Author(SluggedModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email_address = models.EmailField()
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return self.full_name

    # Slug source is derived, so build it explicitly rather than via a field.
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug(self.full_name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("author-posts-page", args=[self.slug])

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(
            status=Post.Status.PUBLISHED, published_at__lte=timezone.now()
        )

    def with_related(self):
        return self.select_related("author").prefetch_related("tags")

    def search(self, term):
        term = (term or "").strip()
        if not term:
            return self.none()
        return self.filter(
            models.Q(title__icontains=term)
            | models.Q(excerpt__icontains=term)
            | models.Q(content__icontains=term)
            | models.Q(tags__caption__icontains=term)
        ).distinct()


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, db_index=True, max_length=100)
    excerpt = models.CharField(max_length=200)
    image = models.ImageField(upload_to="posts", null=True, blank=True)
    focal_point = models.CharField(
        max_length=10,
        choices=FocalPoint.choices,
        default=FocalPoint.TOP,
        help_text=(
            "Pictures are scaled up or down to fill their box; whatever "
            "overflows is trimmed. This picks the edge that must never be "
            "trimmed — the trimming comes off the other sides."
        ),
    )
    content = models.TextField(
        validators=[MinLengthValidator(10)],
        help_text="Markdown is supported.",
    )
    author = models.ForeignKey(
        Author, on_delete=models.SET_NULL, null=True, related_name="posts"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set automatically the first time the post is published.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [models.Index(fields=["-published_at"])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Stamp the publish date once, on the transition into PUBLISHED, so
        # later edits never reshuffle the post ordering.
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        optimize_uploaded_image(self.image)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("post-detail-page", args=[self.slug])

    @property
    def focal_css(self):
        return FocalPoint.to_css(self.focal_point)

    def get_newer_post(self):
        """The next post forward in time, or None at the newest end."""
        return self._neighbour(newer=True)

    def get_older_post(self):
        """The next post back in time, or None at the oldest end."""
        return self._neighbour(newer=False)

    def _neighbour(self, newer):
        if self.published_at is None:
            # An unpublished draft has no place in the timeline.
            return None
        # Several posts can share a publish date (everything migrated from the
        # old `date` field does), so the primary key breaks ties — otherwise
        # stepping through the archive would skip its siblings.
        if newer:
            condition = models.Q(published_at__gt=self.published_at) | models.Q(
                published_at=self.published_at, pk__gt=self.pk
            )
            order = ("published_at", "pk")
        else:
            condition = models.Q(published_at__lt=self.published_at) | models.Q(
                published_at=self.published_at, pk__lt=self.pk
            )
            order = ("-published_at", "-pk")

        return (
            Post.objects.published()
            .filter(condition)
            .exclude(pk=self.pk)
            .order_by(*order)
            .first()
        )

    @property
    def is_published(self):
        return (
            self.status == self.Status.PUBLISHED
            and self.published_at is not None
            and self.published_at <= timezone.now()
        )


class PostImage(models.Model):
    """An extra picture in a post's gallery, beyond the header image."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to="gallery")
    caption = models.CharField(max_length=200, blank=True)
    focal_point = models.CharField(
        max_length=10, choices=FocalPoint.choices, default=FocalPoint.TOP
    )
    sort_order = models.PositiveIntegerField(
        default=0, help_text="Lower numbers appear first."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.caption or f"Image {self.pk} for {self.post}"

    def save(self, *args, **kwargs):
        optimize_uploaded_image(self.image)
        super().save(*args, **kwargs)

    @property
    def focal_css(self):
        return FocalPoint.to_css(self.focal_point)


class CommentQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(is_approved=True)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user_name = models.CharField(max_length=120)
    user_email = models.EmailField()
    text = models.TextField(max_length=400)
    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Comments stay hidden until you approve them.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CommentQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_name} on {self.post}"
