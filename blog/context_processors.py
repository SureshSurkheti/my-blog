from django.conf import settings

from .models import Tag


def blog_settings(request):
    """Site identity and the tag list, available to every template."""
    return {
        "blog": settings.BLOG_SETTINGS,
        "all_tags": Tag.objects.all(),
        "social_links": settings.SOCIAL_LINKS,
    }
