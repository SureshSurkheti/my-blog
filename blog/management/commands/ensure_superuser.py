"""Create or update the one admin account, from the environment.

Render's free tier has no shell, so there is no way to run ``createsuperuser``
against the live database by hand — and ``dumpdata blog`` carries no accounts,
so a rebuilt database comes back with nobody able to log in. The build makes
the account instead, from variables set on the service and never from anything
committed here.

It runs on every deploy and is quiet when nothing needs changing, so the same
command rotates the password: change the variable on the service and redeploy.
The password is read, compared and stored, but never printed.
"""

import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    ValidationError,
    validate_password,
)
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the admin account named by the environment."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username", default=os.environ.get("DJANGO_SUPERUSER_USERNAME")
        )
        parser.add_argument(
            "--password", default=os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        )
        parser.add_argument(
            "--email", default=os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        )

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        email = options["email"] or ""

        if not username or not password:
            self.stdout.write(
                "No admin credentials in the environment — accounts left alone."
            )
            return

        model = get_user_model()
        user, created = model.objects.get_or_create(
            username=username, defaults={"email": email}
        )

        changes = ["created the account"] if created else []

        if not (user.is_staff and user.is_superuser):
            user.is_staff = user.is_superuser = True
            changes.append("granted admin rights")

        # check_password against the stored hash, so an unchanged password
        # costs one comparison and no write.
        if not user.check_password(password):
            user.set_password(password)
            changes.append("set the password")

        if email and user.email != email:
            user.email = email
            changes.append("updated the email address")

        if changes:
            user.save()
            self.stdout.write(f"Admin {username!r}: " + ", ".join(changes) + ".")
        else:
            self.stdout.write(f"Admin {username!r} is already as configured.")

        self._warn_if_weak(password, user)

    def _warn_if_weak(self, password, user):
        """Say so on every deploy, but never refuse to set it.

        The admin is the whole site: anyone who reaches it can publish, edit
        and delete. /admin/ is also the first path automated scanners try, so
        a guessable password here is found in minutes rather than years.
        """
        try:
            validate_password(password, user)
        except ValidationError as problem:
            self.stderr.write("WARNING: this admin password is weak.")
            for message in problem.messages:
                self.stderr.write(f"  - {message}")
