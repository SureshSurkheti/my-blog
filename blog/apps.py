from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

    def ready(self):
        _watch_env_file()


def _watch_env_file():
    """Make `runserver` reload when .env changes.

    Settings read .env once at startup, and the autoreloader only watches
    Python files — so editing .env appeared to do nothing until the server was
    restarted by hand. Adding it to the watch list makes the change take effect
    the same way a code edit does.
    """
    from django.conf import settings

    if not settings.DEBUG:
        return

    from django.utils.autoreload import autoreload_started

    def watch(sender, **kwargs):
        # `extra_files` is the reloader's set of individual paths to watch;
        # there is no public watch_file() on StatReloader.
        extra_files = getattr(sender, "extra_files", None)
        if extra_files is not None:
            extra_files.add(settings.BASE_DIR / ".env")

    autoreload_started.connect(watch, dispatch_uid="blog.watch_env_file")
