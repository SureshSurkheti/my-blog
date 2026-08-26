"""Photo attribution for pictures that are not the site owner's own work.

The seeded posts borrow freely-licensed photographs from Wikimedia Commons.
CC BY and CC BY-SA require credit, but a credit list at the bottom of every
article is noise for a reader — so the credit is collected here and shown on
one page instead, which is a normal and accepted way to satisfy those
licences.

``seed_kyushu`` writes the file; nothing reads it but the credits page.

The page is **not linked from anywhere** — that was a deliberate choice by the
site owner. It stays reachable at /credits, but CC BY and CC BY-SA both require
attribution that a reader can actually find, so the site is only properly clear
of that obligation once these borrowed photographs are replaced with the
owner's own. Delete this file at that point and the page empties out.
"""

import json

from django.conf import settings

ATTRIBUTIONS_PATH = settings.BASE_DIR / "blog" / "photo_credits.json"


def load():
    """Every credited photo, newest post first.

    Returns an empty list when the file is absent, so a blog with only its
    owner's photographs simply has no credits page.
    """
    if not ATTRIBUTIONS_PATH.exists():
        return []

    entries = json.loads(ATTRIBUTIONS_PATH.read_text())
    rows = [{"file": name, **data} for name, data in entries.items()]
    rows.sort(key=lambda row: (row["post"], row["file"]))
    return rows


def grouped():
    """The same credits, gathered under the post each picture appears in."""
    groups = {}
    for row in load():
        groups.setdefault((row["post"], row["post_url"]), []).append(row)
    return [
        {"title": title, "url": url, "photos": photos}
        for (title, url), photos in groups.items()
    ]
