"""Download the Wikimedia Commons photographs the Kyushu seed posts use.

Kept separate from ``seed_kyushu`` so the network step runs once and the
seeding step stays offline and repeatable. Every file is checked against an
allow-list of free licences before it is saved, and the credit line Commons
returns is written to ``credits.json`` beside the images.
"""

import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from blog.seed_data import POSTS

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "SureshBlogSeed/1.0 (personal blog seeding; Django management command)"

# Licences that permit reuse with attribution. Anything outside this list is
# refused rather than downloaded — a non-free photo on a public blog is a
# problem, and a missing photo is only an inconvenience.
FREE_LICENCE_PREFIXES = ("cc0", "cc by", "public domain", "pd-", "pd ")

# ...but not every "CC BY" is usable here. NC forbids commercial use, and ND
# forbids derivatives — and every photo goes through the resize-and-re-encode
# pipeline, which produces one. Both are refused.
BLOCKED_LICENCE_CLAUSES = ("-nc", "-nd", " nc", " nd", "noncommercial", "noderiv")

TAG_RE = re.compile(r"<[^>]+>")


def is_free_licence(licence):
    """True when this licence allows reuse, with credit, of a resized copy."""
    text = (licence or "").strip().lower()
    if not text.startswith(FREE_LICENCE_PREFIXES):
        return False
    return not any(clause in text for clause in BLOCKED_LICENCE_CLAUSES)


def _plain(value):
    """Commons returns small HTML fragments; keep only the text."""
    return html.unescape(TAG_RE.sub("", value or "")).strip()


def _slugify_filename(commons_title):
    stem = Path(commons_title).stem
    suffix = Path(commons_title).suffix.lower() or ".jpg"
    safe = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return f"{safe[:80]}{suffix}"


class Command(BaseCommand):
    help = "Download the Commons photos referenced by blog/seed_data.py."

    def add_arguments(self, parser):
        parser.add_argument(
            "--photos",
            default="seed_photos",
            help="Directory to download into (default: seed_photos).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-download files that are already present.",
        )

    def handle(self, *args, **options):
        photo_dir = Path(options["photos"])
        photo_dir.mkdir(parents=True, exist_ok=True)

        titles = []
        for post in POSTS:
            for name in [post["image"], *(g[0] for g in post["gallery"])]:
                if name not in titles:
                    titles.append(name)

        self.stdout.write(f"{len(titles)} unique photos to resolve.")
        credits = self._load_credits(photo_dir)

        for index, title in enumerate(titles, start=1):
            local = _slugify_filename(title)
            target = photo_dir / local
            if target.exists() and not options["force"] and title in credits:
                self.stdout.write(f"  [{index:>2}/{len(titles)}] have {local}")
                continue

            info = self._imageinfo(title)
            licence = _plain(
                info["extmetadata"].get("LicenseShortName", {}).get("value")
            )
            if not is_free_licence(licence):
                raise CommandError(f"{title!r} is licensed {licence!r} — refusing it.")

            url = info.get("thumburl") or info["url"]
            data = self._download(url)
            target.write_bytes(data)

            credits[title] = {
                "file": local,
                "artist": _plain(info["extmetadata"].get("Artist", {}).get("value"))
                or "Unknown",
                "licence": licence,
                "licence_url": _plain(
                    info["extmetadata"].get("LicenseUrl", {}).get("value")
                ),
                "source": info["descriptionurl"],
            }
            self.stdout.write(
                f"  [{index:>2}/{len(titles)}] {local} "
                f"({len(data) // 1024} KB, {licence})"
            )
            self._save_credits(photo_dir, credits)
            time.sleep(0.6)  # be polite to Commons

        self._save_credits(photo_dir, credits)
        self.stdout.write(
            self.style.SUCCESS(f"Done. {len(credits)} photos in {photo_dir}/")
        )

    # -- Commons plumbing -------------------------------------------------

    def _api(self, params):
        url = f"{API}?{urllib.parse.urlencode(params)}"
        return json.loads(self._download(url).decode("utf-8"))

    def _download(self, url):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    return response.read()
            except urllib.error.HTTPError as exc:
                # Commons throttles hard; back off rather than give up.
                if exc.code != 429 or attempt == 5:
                    raise
                time.sleep(4 * (attempt + 1))
        raise CommandError(f"gave up downloading {url}")

    def _imageinfo(self, title):
        data = self._api(
            {
                "action": "query",
                "format": "json",
                "titles": f"File:{title}",
                "prop": "imageinfo",
                "iiprop": "url|extmetadata|size",
                "iiurlwidth": "1600",
            }
        )
        pages = list(data.get("query", {}).get("pages", {}).values())
        if not pages or "imageinfo" not in pages[0]:
            raise CommandError(f"Commons has no file named {title!r}")
        return pages[0]["imageinfo"][0]

    # -- credits.json -----------------------------------------------------

    @staticmethod
    def _credits_path(photo_dir):
        return photo_dir / "credits.json"

    def _load_credits(self, photo_dir):
        path = self._credits_path(photo_dir)
        return json.loads(path.read_text()) if path.exists() else {}

    def _save_credits(self, photo_dir, credits):
        self._credits_path(photo_dir).write_text(
            json.dumps(credits, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        )
