# Suresh' Blog

A personal travel and tech blog built with Django 5.2 — Markdown posts,
drafts, photo galleries, moderated comments, tags, search, a session-based
reading list, and RSS/Atom feeds.

## Requirements

- Python 3.13 (3.12 also works)
- No external services: it runs on SQLite out of the box

## Quick start

```bash
make install          # create .venv and install dependencies
cp .env.example .env  # adjust if you like; the defaults work for local dev
make migrate
make superuser        # create your admin login
make run              # http://127.0.0.1:8001
```

Without `make`:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver 8001
```

## Everyday commands

| Command         | What it does                                  |
| --------------- | --------------------------------------------- |
| `make run`      | Development server on :8001                   |
| `make test`     | Full test suite                               |
| `make coverage` | Tests plus a coverage report                  |
| `make lint`     | Ruff lint + format check                      |
| `make format`   | Auto-format and auto-fix                      |
| `make check`    | Django system checks + migration drift check  |
| `make help`     | List every target                             |

## Writing posts

Everything is managed at `/admin/`.

1. Create an **Author** and some **Tags** (slugs fill in automatically).
2. Create a **Post**. The body accepts **Markdown** — headings, lists, links,
   tables and fenced code blocks all work. Rendered HTML is sanitized, so a
   post can never inject scripts into the page.
3. Leave **Status** as *Draft* while you work. Nothing appears on the site
   until you switch it to *Published*.
4. `published_at` is stamped once, the first time a post goes live, so later
   edits never reshuffle the ordering. You can set it to a future date to
   schedule a post — it stays hidden until then.

Logged-in staff can open a draft's URL directly to preview it; visitors get a
404. The admin list has bulk **Publish** / **Move back to draft** actions.

### Pictures

Each post has one **header picture** plus a **gallery** of any number of extra
photos, both uploaded from the post's admin page (the gallery is the inline
table at the bottom — add a caption and a sort order for each).

Every upload is processed on save:

- rotated upright from its EXIF orientation flag
- scaled down so the longest edge is at most `IMAGE_MAX_DIMENSION` (1600px by
  default, and never scaled *up*)
- re-compressed to `IMAGE_JPEG_QUALITY` (80 by default, progressive)
- stripped of all metadata, **including GPS coordinates** — worth knowing for
  travel photos taken on a phone
- opaque PNGs are converted to JPEG; genuine transparency stays PNG

Editing a post later never re-compresses an already-stored picture.

**Fitting.** Every picture box is a fixed size — 13rem tall on post cards,
11rem on gallery tiles, 12rem square on the post header — and the photo fills
it completely (`object-fit: cover`), so there is never empty space in a card.
To never crop instead (whole picture visible, letterboxed), change that one
line in `blog/static/blog/post.css` to `object-fit: contain`.

**Cropping.** A picture is scaled up or down until it fills its box, and
whichever dimension still overflows is trimmed. Which dimension that is depends
on the photo's shape, so trimming can come off the sides, the bottom, or the
top. The **focal point** picks the edge that must survive; the trim is taken
from the others.

It defaults to **Keep the top**, so with a 342x208 box:

| Photo shape        | Trimmed from       | Kept intact         |
| ------------------ | ------------------ | ------------------- |
| Wide (e.g. 1200x400)  | left **and** right | top, bottom         |
| Tall (e.g. 400x1200)  | bottom             | top, left, right    |
| Same shape as box  | nothing            | all of it           |

So faces, skylines and mountain peaks at the top of a photo are never cut,
while the sides and the bottom give way as needed. Change the focal point on an
individual picture when a different edge is the one that matters. This is an
edge choice, not a drag-a-box crop tool.

**Viewing.** Clicking any gallery photo opens a full-screen viewer with
previous/next controls on the left and right, arrow-key navigation, and Escape
or a backdrop click to close. It wraps around at both ends. Without JavaScript
each thumbnail stays a plain link to the full-size file.

**Pictures inside the body.** Post bodies are Markdown, so a picture anywhere
in the text is just `![description](/files/posts/photo.jpg)`. You don't have to
find that URL by hand: the admin shows a ready-to-paste snippet under
**Paste into the body** for the header picture and for every gallery photo —
click it to select, copy, and drop it wherever you want in the text.

### Comments

Comments are **moderated**: a new comment is saved but hidden, and the
commenter is told it will appear once approved. Approve them in the admin
(`/admin/blog/comment/`) individually or with the bulk **Approve selected
comments** action. A hidden honeypot field silently discards bot submissions.

### Code blocks

Fenced code blocks are syntax-highlighted with Pygments. To change the theme,
regenerate the stylesheet:

```bash
.venv/bin/python -c "from pygments.formatters import HtmlFormatter; \
  print(HtmlFormatter(style='monokai', cssclass='codehilite').get_style_defs())"
```

then paste the output under the hand-written container rules in
`static/pygments.css`.

## Routes

| Path                | Page                                        |
| ------------------- | ------------------------------------------- |
| `/`                 | Home — the latest posts                     |
| `/posts`            | All posts, paginated                        |
| `/posts/<slug>`     | A single post, with comments                |
| `/tags/<slug>`      | Posts carrying one tag                      |
| `/authors/<slug>`   | Posts by one author                         |
| `/search?q=`        | Search titles, excerpts, bodies and tags    |
| `/read-later`       | Saved posts (session-based, no login)       |
| `/feed/rss`         | RSS feed                                    |
| `/feed/atom`        | Atom feed                                   |
| `/sitemap.xml`      | Sitemap for search engines                  |
| `/admin/`           | Django admin                                |

## Configuration

Settings that vary by machine live in `.env` (git-ignored). See
`.env.example` for the full list; the useful ones:

| Variable                  | Default              | Purpose                              |
| ------------------------- | -------------------- | ------------------------------------ |
| `DEBUG`                   | `False`              | Never leave this on in production     |
| `SECRET_KEY`              | random in DEBUG      | **Required** when `DEBUG=False`       |
| `ALLOWED_HOSTS`           | `127.0.0.1,localhost`| Comma-separated hostnames            |
| `DATABASE_URL`            | local SQLite         | e.g. `postgres://user:pw@host/db`    |
| `TIME_ZONE`               | `UTC`                | Used for display and stamping        |
| `BLOG_TITLE`              | `Suresh's Blog`      | Shown in the header, feeds and tabs  |
| `BLOG_POSTS_PER_PAGE`     | `6`                  | Pagination size                       |
| `IMAGE_MAX_DIMENSION`     | `1600`               | Longest edge kept on upload           |
| `IMAGE_JPEG_QUALITY`      | `80`                 | JPEG quality on upload                |
| `MEDIA_ROOT`              | `uploads/`           | Where uploads are written             |
| `BLOG_LATEST_POSTS_COUNT` | `3`                  | Posts shown on the homepage          |

HTTPS-only protections (SSL redirect, secure cookies, HSTS) switch on
automatically whenever `DEBUG=False`, so local HTTP development is unaffected.

## Project layout

```
blog/
  models.py          Post, PostImage, Comment, Tag, Author + querysets
  imaging.py         Upload-time resize/compress/EXIF-strip pipeline
  views.py           Page views; PublishedPostListView is the shared list base
  forms.py           Comment form with validation and a spam honeypot
  feeds.py           RSS and Atom feeds
  sitemaps.py        sitemap.xml entries
  admin.py           Admin config: gallery inline, publish/approve actions
  context_processors.py  Site title/description and the tag list, site-wide
  templatetags/blog_extras.py  markdown, reading_time, query_replace
  templates/blog/    Page templates and includes
  static/blog/       Per-page CSS
  migrations/        0006-0008 publishing; 0009-0010 gallery + moderation;
                     0011-0012 focal point defaults
  tests/             145 tests: models, views, filters, feeds, admin, uploads
my_site/
  settings.py        Single env-driven settings module
  social.py          Builds the social profile links from the environment
  urls.py            Root URLs, sitemap wiring
  test_runner.py     Quiet logging + fast password hashing under test
templates/           base.html and the 403/404/500 pages
static/app.css       Shared styling
static/gallery.js    Gallery lightbox (progressive enhancement)
static/nav.js        Collapses the header search into an icon
static/pygments.css  Generated syntax-highlighting theme
static/favicon.*     Site icons (see scripts/make_favicon.py)
```

## Social profiles

Set the handles you want in `.env` — a bare handle is enough, and the URL is
built for you:

```
SOCIAL_INSTAGRAM=@yourhandle
SOCIAL_FACEBOOK=your.profile
SOCIAL_TIKTOK=@yourhandle
SOCIAL_LINKEDIN=your-profile-slug
SOCIAL_X=yourhandle
SOCIAL_YOUTUBE=yourchannel
SOCIAL_GITHUB=oec-suresh
SOCIAL_MASTODON=https://mastodon.social/@you   # full URL
SOCIAL_WEBSITE=https://example.com             # full URL
```

They appear in the order listed above.

Anything left blank or commented out simply does not appear, so the site
renders cleanly with none of them set. `runserver` watches `.env`, so a change
takes effect on its own — no manual restart. (That relies on
`read_env(..., overwrite=True)` in settings: the autoreloader re-executes with
the parent's environment, and without `overwrite` django-environ's setdefault
semantics would keep the stale values. Production supplies real environment
variables and ships no `.env`, so there is nothing there for it to override.) Configured links show in the footer of every page and again
under the homepage bio. They carry `rel="me"`, which lets those profiles verify
this site as yours, and `noopener` for safety.

The links are text labels rather than brand icons, deliberately: an icon-only
row needs correct official SVG artwork, and a mangled logo looks worse than a
word. If you want real icons, paste the official SVG paths (e.g. from
simple-icons) and I'll swap them in.

Only link accounts you actually post to — a stale profile costs more
credibility than no link. Note that the site already shows your photo, your
city and your profession, so linking personal accounts ties all of that to a
findable identity. Your author email address is stored in the database but is
deliberately **not** rendered anywhere, and adding a raw `mailto:` link would
expose it to scrapers.

## Site icons

`static/favicon.ico` is the source of truth. Every other size is generated from
it, so all screen types are covered:

| File | Used by |
| ---- | ------- |
| `favicon.ico` | Browser tabs, older browsers (16/32/48 in one file) |
| `favicon-32.png` | Browsers that prefer a PNG |
| `apple-touch-icon.png` | iOS home screen (180px, alpha flattened) |
| `icon-192.png`, `icon-512.png` | Android and installable web apps |
| `site.webmanifest` | App name, theme colour, icon list |

Regenerate after replacing the icon:

```bash
.venv/bin/python scripts/make_favicon.py
```

The script also reads the icon's dominant colour and writes it into the
manifest as the theme colour. `/favicon.ico` is routed at the root as well,
since browsers request it there whatever the link tags say.

**For sharp large icons**, drop a square `static/favicon-source.png` at 512px or
larger next to the .ico and re-run. The script prefers it and rebuilds the .ico
from it too. Without one it falls back to the .ico's largest frame — usually
48px — and upscales, which the 180px and 512px icons show as softness. The
script prints a warning when that happens.

## Getting around

There is deliberately **no "Back" button** — browsers already have one, and a
button that only calls `history.back()` is unreliable (it does nothing for
someone arriving from a search result or a shared link). Instead the site
offers navigation that always knows where it goes:

- **"← All posts"** above every post, for returning to the archive
- a **"Keep reading"** panel at the end of each article with the neighbouring
  posts as cards (thumbnail, title and date), and a "See all posts" link. A
  missing neighbour is omitted rather than shown as an empty placeholder, and
  the whole panel is hidden when a post has no neighbours at all
- The header's **All Posts** link and the tag pills on every list page

Neighbours are worked out from `published_at`, with the primary key breaking
ties — several posts share a timestamp (everything migrated from the old `date`
field does), and without the tie-break stepping through the archive would skip
its siblings. Drafts and future-dated posts are never neighbours.

## Header

The header is **in the flow and sticky** — `position: sticky; top: 0` — not
absolutely positioned. That matters for two reasons: it stays reachable while
scrolling a long photo post, and pages no longer need hand-tuned top margins to
clear it. Those margins were the cause of a 104px gap above the post hero, and
that class of bug would have recurred with every new element added at the top
of a page.

Its background is defined **once** in `static/app.css`. Previously each page's
own stylesheet painted it, so the homepage (which never did) had a header that
was invisible against white on mobile. Where `backdrop-filter` is supported the
bar is translucent and blurs what's behind it, which keeps the homepage
gradient continuous.

- 64px tall on desktop, **56px on mobile** (it was 161px — a fifth of a phone
  screen — when the title, links and search each had their own row)
- the search box collapses to an icon that expands on click, focuses the field,
  and closes on Escape or a click outside. With JavaScript disabled the form
  simply stays visible and works as a plain search box
- the current section is underlined and carries `aria-current="page"` — the
  archive link covers post, tag, author and search pages
- "All Posts" shortens to "Posts" on phones so everything fits one row at 320px
- the site title scales with `clamp()` and changes colour on hover rather than
  underlining (an underline under a large title read as heavy); keyboard focus
  still gets a visible ring

The reading list is called **Saved** everywhere — the nav link, the page
heading, the browser tab, and the confirmation message. The button on a post is
the matching verb form ("Save for later" / "Remove from saved"). It previously
went by four different names in four places: "Stored Posts", "Saved", "Read
Later" and "My Stored Posts".

## Mobile

The layout is responsive down to 320px wide. The breakpoint is **48rem**
(768px), and below it:

- post cards drop to a single full-width column
- the post hero, gallery, comments and comment form go full-width, and the
  author card moves below the title instead of beside it
- interactive controls — nav links, pagination, buttons, form fields, the
  lightbox arrows — are at least 2.75rem (44px) tall
- form fields are 16px, which stops iOS Safari zooming in on focus
- wide tables and code blocks scroll inside their own box rather than pushing
  the page sideways

Verified with no horizontal overflow at 320px, 390px and 768px on every page.

## Notes

- `db.sqlite3` is git-ignored — the database is local data, not source. Keep
  your own backups (`cp db.sqlite3 db.backup.sqlite3`) before migrating.
- Uploaded images live in `uploads/` and *are* tracked, since they're the
  content of existing posts.
- The "A Little About Me" copy on the homepage is hand-written in
  `blog/templates/blog/index.html` — edit it there. The site title and tagline
  come from `.env` instead.
- The `SECRET_KEY` that used to be hardcoded in `settings.py` is still in the
  git history. It was only ever a development key, but if this ever goes
  public, generate a fresh one for the deployed site.
