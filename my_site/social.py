"""Build the site's social profile links from the environment.

Each platform is read from ``SOCIAL_<PLATFORM>``. A value may be a bare handle
(``sureshsurkheti``, or ``@sureshsurkheti``) which is expanded with the
platform's URL pattern, or a full URL for anything self-hosted. Platforms left
blank are skipped entirely, so nothing renders until a handle is set.
"""

# key, display label, URL pattern ("" means a full URL is required)
# Order here is the order they appear on the page.
PLATFORMS = (
    ("instagram", "Instagram", "https://www.instagram.com/{}"),
    ("facebook", "Facebook", "https://www.facebook.com/{}"),
    ("tiktok", "TikTok", "https://www.tiktok.com/@{}"),
    ("linkedin", "LinkedIn", "https://www.linkedin.com/in/{}"),
    ("x", "X", "https://x.com/{}"),
    ("youtube", "YouTube", "https://www.youtube.com/@{}"),
    ("github", "GitHub", "https://github.com/{}"),
    ("mastodon", "Mastodon", ""),
    ("website", "Website", ""),
)


def build_social_links(env):
    """Return ``[{"key", "label", "url"}, ...]`` for the configured platforms."""
    links = []
    for key, label, pattern in PLATFORMS:
        value = env(f"SOCIAL_{key.upper()}", default="").strip()
        if not value:
            continue

        if value.startswith(("http://", "https://")):
            url = value
        elif pattern:
            url = pattern.format(value.lstrip("@"))
        else:
            # No pattern to expand a bare handle with (Mastodon instances and
            # personal sites differ), so a full URL is required here.
            continue

        links.append({"key": key, "label": label, "url": url})
    return links
