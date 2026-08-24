import logging

from django.conf import settings
from django.test.runner import DiscoverRunner


class QuietTestRunner(DiscoverRunner):
    """Default runner for this project.

    Silences log output (tests deliberately request missing pages, and those
    404 warnings are noise) and swaps in a fast password hasher so the tests
    that log in don't pay for 600k PBKDF2 iterations.
    """

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        logging.disable(logging.CRITICAL)
        settings.PASSWORD_HASHERS = [
            "django.contrib.auth.hashers.MD5PasswordHasher",
        ]

    def teardown_test_environment(self, **kwargs):
        logging.disable(logging.NOTSET)
        super().teardown_test_environment(**kwargs)
