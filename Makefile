# Convenience targets. Everything runs inside the local .venv.
PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help install run test coverage lint format migrate superuser check clean

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
