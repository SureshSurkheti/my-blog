from django.conf import settings

from . import seo
from .models import Tag


def blog_settings(request):
    """Site identity and the tag list, available to every template."""
    return {
        "blog": settings.BLOG_SETTINGS,
        "all_tags": Tag.objects.all(),
        "social_links": settings.SOCIAL_LINKS,
        # A default so every page carries complete tags; views that know more
        # about the page pass their own `seo` and shadow this.
        "seo": seo.build(request),
    }
