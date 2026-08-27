# Convenience targets. Everything runs inside the local .venv.
PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help install run test coverage lint format backup migrate superuser check clean

help:
	@grep -E '^[a-z-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Create the venv and install dependencies
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

run: ## Start the development server on :8001
	$(PY) manage.py runserver 8001

test: ## Run the test suite
	$(PY) manage.py test

coverage: ## Run the tests and report coverage
	.venv/bin/coverage run manage.py test
	.venv/bin/coverage report

lint: ## Check formatting and lint rules
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

format: ## Auto-format and auto-fix
	.venv/bin/ruff format .
	.venv/bin/ruff check --fix .

backup: ## Refresh blog/fixtures/content.json from the database
	@# build.sh restores this fixture into an empty database, so it is what a
	@# fresh deploy — or a replaced Postgres — comes back as. Nothing updates
	@# it on its own; it is only ever as current as the last run of this.
	@#
	@# It dumps whatever DATABASE_URL points at, which by default is the local
	@# SQLite file. Posts written through the live admin live in Render's
	@# Postgres and are NOT in that, so to capture those, run this against the
	@# database's External Connection String from the Render dashboard:
	@#
	@#     DATABASE_URL='postgres://...' make backup
	@#
	@# (Render's free tier has no shell, so this is the way in.)
	@#
	@# Written to a temporary file and moved into place only once the dump has
	@# succeeded. `dumpdata -o` truncates its target before it has connected to
	@# anything, so pointing it straight at the fixture means a failed backup
	@# destroys the backup you already had.
	@echo "  source: $${DATABASE_URL:-local db.sqlite3}" | sed 's|://[^@]*@|://***@|'
	@$(PY) manage.py dumpdata blog --indent 2 -o blog/fixtures/.content.json.tmp
	@mv blog/fixtures/.content.json.tmp blog/fixtures/content.json
	@echo "  $$(grep -c '"blog.post"' blog/fixtures/content.json) posts captured — commit the file"

migrate: ## Apply database migrations
	$(PY) manage.py migrate

superuser: ## Create an admin user
	$(PY) manage.py createsuperuser

check: ## Django system checks, including deployment checks
	$(PY) manage.py check
	$(PY) manage.py makemigrations --check --dry-run

clean: ## Remove caches
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .ruff_cache htmlcov .coverage
