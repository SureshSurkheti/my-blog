"""The only way an admin account reaches the live site.

``dumpdata blog`` carries no accounts and Render's free tier has no shell, so
a rebuilt database has nobody who can log in and no way to fix that by hand.
"""

from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

User = get_user_model()

STRONG = "correct-horse-battery-staple-42"


class EnsureSuperuserTests(TestCase):
    def _run(self, **options):
        out, err = StringIO(), StringIO()
        call_command("ensure_superuser", stdout=out, stderr=err, **options)
        return out.getvalue() + err.getvalue()

    def test_it_creates_the_account_when_there_is_none(self):
        self._run(username="suresh", password=STRONG)

        user = User.objects.get(username="suresh")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password(STRONG))

    def test_a_second_run_changes_nothing(self):
        self._run(username="suresh", password=STRONG)

        output = self._run(username="suresh", password=STRONG)

        self.assertIn("already as configured", output)
        self.assertEqual(User.objects.count(), 1)

    def test_changing_the_variable_rotates_the_password(self):
        self._run(username="suresh", password=STRONG)

        self._run(username="suresh", password="a-different-long-passphrase")

        user = User.objects.get(username="suresh")
        self.assertTrue(user.check_password("a-different-long-passphrase"))
        self.assertFalse(user.check_password(STRONG))

    def test_an_existing_ordinary_user_is_promoted(self):
        User.objects.create_user("suresh", password=STRONG)

        self._run(username="suresh", password=STRONG)

        user = User.objects.get(username="suresh")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_it_does_nothing_without_credentials(self):
        output = self._run(username=None, password=None)

        self.assertIn("accounts left alone", output)
        self.assertEqual(User.objects.count(), 0)

    def test_a_username_without_a_password_is_not_enough(self):
        output = self._run(username="suresh", password=None)

        self.assertIn("accounts left alone", output)
        self.assertEqual(User.objects.count(), 0)

    def test_the_password_is_never_printed(self):
        secret = "a-very-distinctive-passphrase-here"

        output = self._run(username="suresh", password=secret)

        self.assertNotIn(secret, output)

    def test_a_weak_password_is_warned_about_but_still_set(self):
        output = self._run(username="suresh", password="suresh")

        self.assertIn("WARNING", output)
        self.assertIn("too short", output)
        self.assertTrue(User.objects.get(username="suresh").check_password("suresh"))

    def test_a_strong_password_draws_no_warning(self):
        output = self._run(username="suresh", password=STRONG)

        self.assertNotIn("WARNING", output)

    def test_credentials_are_read_from_the_environment(self):
        # This is how the deploy supplies them; nothing is committed.
        env = {
            "DJANGO_SUPERUSER_USERNAME": "suresh",
            "DJANGO_SUPERUSER_PASSWORD": STRONG,
            "DJANGO_SUPERUSER_EMAIL": "suresh@example.com",
        }
        with mock.patch.dict("os.environ", env, clear=False):
            self._run()

        user = User.objects.get(username="suresh")
        self.assertTrue(user.check_password(STRONG))
        self.assertEqual(user.email, "suresh@example.com")
