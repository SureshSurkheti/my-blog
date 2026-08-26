"""
Django settings for my_site.

Values that differ between machines or must stay secret are read from the
environment (see ``.env.example``). Everything else is a project decision and
lives here in version control.
"""

from pathlib import Path

import environ

from .social import build_social_links

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
    SECRET_KEY=(str, ""),
)
# overwrite=True matters for `runserver`: the autoreloader re-executes the
# process with the parent's environment, which already holds whatever the
# previous read injected. Without it, django-environ's setdefault semantics
# keep those stale values and edits to .env appear to do nothing until a full
# manual restart. .env is git-ignored, so production supplies real environment
# variables and ships no file for this to override.
environ.Env.read_env(BASE_DIR / ".env", overwrite=True)

DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# In DEBUG an ephemeral key is fine; a real deployment must supply its own.
SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        from django.core.management.utils import get_random_secret_key

        SECRET_KEY = get_random_secret_key()
    else:
        raise environ.ImproperlyConfigured(
            "SECRET_KEY must be set in the environment when DEBUG is off."
        )


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "cloudinary_storage",
    "django.contrib.staticfiles",
    "cloudinary",
    "blog",
    "django.contrib.sitemaps",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware", 
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "my_site.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "my_site.wsgi.application"
ASGI_APPLICATION = "my_site.asgi.application"


# Database

DATABASES = {
    "default": env.db_url(
        "DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True


# Static files and uploads

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

STATICFILES_STORAGE = STORAGES["staticfiles"]["BACKEND"]

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": env("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": env("CLOUDINARY_API_KEY"),
    "API_SECRET": env("CLOUDINARY_API_SECRET"),
}

# Configurable so a throwaway/demo run can be pointed at a scratch directory
# instead of writing into (or cleaning up) the real uploads.
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "uploads"))
MEDIA_URL = "files/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEST_RUNNER = "my_site.test_runner.QuietTestRunner"


# Blog-specific settings, surfaced to templates by blog.context_processors

BLOG_SETTINGS = {
    "title": env("BLOG_TITLE", default="Suresh's Blog"),
    "description": env(
        "BLOG_DESCRIPTION",
        default="A software engineer in Japan, writing about the places I visit.",
    ),
    "posts_per_page": env.int("BLOG_POSTS_PER_PAGE", default=6),
    "latest_posts_count": env.int("BLOG_LATEST_POSTS_COUNT", default=6),
}

TEMPLATES[0]["OPTIONS"]["context_processors"].append(
    "blog.context_processors.blog_settings"
)

# Social profiles shown in the footer and the homepage bio. Anything not set in
# the environment is simply absent.
SOCIAL_LINKS = build_social_links(env)


# Uploaded images are re-encoded on save (see blog/imaging.py). 1600px is
# ample for a full-width photo on this layout; raise it only if you need to.

IMAGE_UPLOAD = {
    "max_dimension": env.int("IMAGE_MAX_DIMENSION", default=1600),
    "jpeg_quality": env.int("IMAGE_JPEG_QUALITY", default=80),
}


# Security. The HTTPS-dependent settings are only switched on outside DEBUG so
# that local development over plain HTTP keeps working.

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}
