"""Connection reuse, which is applied to a remote database and not to SQLite."""

from django.test import TestCase

from my_site.settings import reuse_connections

POSTGRES = "django.db.backends.postgresql"
SQLITE = "django.db.backends.sqlite3"


class ReuseConnectionsTests(TestCase):
    def test_postgres_holds_the_connection_open(self):
        config = reuse_connections({"ENGINE": POSTGRES}, 600)

        self.assertEqual(config["CONN_MAX_AGE"], 600)

    def test_postgres_checks_the_connection_is_still_alive(self):
        # Without this a dropped connection surfaces as a 500 on the next
        # request rather than being quietly reopened.
        config = reuse_connections({"ENGINE": POSTGRES}, 600)

        self.assertTrue(config["CONN_HEALTH_CHECKS"])

    def test_sqlite_is_left_exactly_as_it_was(self):
        config = reuse_connections({"ENGINE": SQLITE}, 600)

        self.assertEqual(config, {"ENGINE": SQLITE})

    def test_the_age_is_whatever_it_is_given(self):
        config = reuse_connections({"ENGINE": POSTGRES}, 30)

        self.assertEqual(config["CONN_MAX_AGE"], 30)

    def test_other_settings_survive(self):
        config = reuse_connections({"ENGINE": POSTGRES, "NAME": "blog"}, 600)

        self.assertEqual(config["NAME"], "blog")
