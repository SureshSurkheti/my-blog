#!/usr/bin/env bash
# Render build command. Set this as the service's "Build Command":
#
#     ./build.sh
#
# Everything here must be safe to run on every deploy, because it does.
set -o errexit

pip install -r requirements.txt

# Hashed filenames for the manifest storage. Without this the pages render but
# every stylesheet 404s, because the templates ask for names that don't exist.
python manage.py collectstatic --no-input

# The database ships empty — db.sqlite3 is gitignored, so a fresh deploy has no
# tables at all and every page 500s with "no such table: blog_post".
python manage.py migrate --no-input

# Seed the content, but only into an empty database. loaddata overwrites by
# primary key, so running it unconditionally would silently revert every post
# edited in the admin since the fixture was dumped — on every single deploy.
# Asked via django.setup() rather than `manage.py shell -c`, which prints an
# auto-import banner to stdout ahead of the answer and breaks the comparison.
post_count=$(python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_site.settings')
django.setup()
from blog.models import Post
print(Post.objects.count())
")

if [ "$post_count" = "0" ]; then
  echo "Empty database — loading initial content."
  python manage.py loaddata content
else
  echo "Database already has posts — leaving content alone."
fi

# A rebuilt database carries the image *paths* but not the image *files*:
# loaddata restores every row and nothing puts the photographs back, so the
# posts render perfectly with a broken picture on each one. This re-uploads
# only what storage is actually missing, and does nothing once they're there.
python manage.py restore_media --fetch

# Nobody can log in to a rebuilt database: `dumpdata blog` carries no accounts
# and the free tier has no shell to run createsuperuser from. The credentials
# come from the service's environment, never from this repository, and the
# command is quiet unless something actually changed.
python manage.py ensure_superuser
