"""The light/dark switch, and the one duplication CSS leaves no way around."""

import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase

CSS = Path(settings.BASE_DIR) / "static" / "app.css"
JS = Path(settings.BASE_DIR) / "static" / "theme.js"


def tokens_in(block):
    """Token names and values, ignoring comments.

    Without stripping them, a comment mentioning a token by name reads as a
    declaration and swallows everything up to the next semicolon — which is
    exactly what happened while fixing the invisible body text.
    """
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
    return dict(re.findall(r"(--[a-z-]+):\s*([^;]+);", block))


class ThemeTokensTests(TestCase):
    """The dark palette is written twice: once for the system preference and
    once for an explicit choice. A declaration block cannot be shared between
    a media query and a plain selector, so the copies have to match by hand —
    which is exactly the kind of thing that rots silently."""

    def setUp(self):
        css = CSS.read_text()
        media = css[css.index('@media (prefers-color-scheme: dark)'):]
        self.from_system = tokens_in(media[media.index("{"):media.index("\n  }")])
        explicit = css[css.index(':root[data-theme="dark"] {'):]
        self.from_choice = tokens_in(explicit[: explicit.index("\n}")])

    def test_both_copies_define_the_same_tokens(self):
        self.assertEqual(
            sorted(self.from_system), sorted(self.from_choice),
            "the two dark palettes no longer define the same tokens",
        )

    def test_both_copies_give_them_the_same_values(self):
        for name in sorted(self.from_system):
            with self.subTest(token=name):
                self.assertEqual(self.from_system[name], self.from_choice[name])

    def test_the_palette_is_not_empty(self):
        # A mis-sliced parse would make the two tests above pass trivially.
        self.assertGreater(len(self.from_system), 40)

    def test_every_dark_token_exists_in_the_light_palette(self):
        css = CSS.read_text()
        # Start the search for the closing brace at :root — the first "\n}"
        # in the file closes an @font-face block further up.
        start = css.index(":root {")
        light = tokens_in(css[start : css.index("\n}", start)])

        missing = sorted(set(self.from_system) - set(light))

        self.assertEqual(missing, [], "dark overrides a token light never sets")


class ThemeOverrideTests(TestCase):
    def test_an_explicit_light_choice_beats_a_dark_system(self):
        # Without the :not(), a reader on a dark phone who asked for light
        # would still be served dark and the button would look broken.
        css = CSS.read_text()
        media = css[css.index("@media (prefers-color-scheme: dark)"):]

        self.assertIn(':root:not([data-theme="light"])', media)

    def test_the_media_query_does_not_target_bare_root(self):
        css = CSS.read_text()
        media = css[css.index("@media (prefers-color-scheme: dark)"):]
        head = media[: media.index("{", media.index("{") + 1)]

        self.assertNotRegex(head, r":root\s*\{")


class ThemeMarkupTests(TestCase):
    def test_the_choice_is_applied_before_the_first_paint(self):
        # In an external file this runs after the first paint, and a reader
        # who chose dark sees a white flash before the page catches up.
        body = self.client.get("/").content.decode()
        head = body[: body.index("</head>")]

        self.assertIn("localStorage.getItem(\"theme\")", head)
        self.assertLess(head.index("localStorage"), head.index("app"))

    def test_the_button_ships_hidden(self):
        # Revealed by theme.js. With JavaScript off it cannot work, and a
        # dead control is worse than no control.
        body = self.client.get("/").content.decode()
        start = body.rindex("<button", 0, body.index("data-theme-toggle"))
        tag = body[start : body.index(">", start) + 1]

        self.assertIn("hidden", tag)

    def test_the_button_says_what_it_will_do(self):
        body = self.client.get("/").content.decode()

        self.assertIn('aria-label="Switch to dark mode"', body)

    def test_the_script_is_loaded(self):
        self.assertContains(self.client.get("/"), "theme")

    def test_the_inline_script_survives_storage_being_blocked(self):
        # Private browsing throws on localStorage access; an uncaught error
        # here would stop every later script on the page.
        body = self.client.get("/").content.decode()
        head = body[: body.index("</head>")]
        snippet = head[head.index("localStorage") - 200 : head.index("</script>")]

        self.assertIn("try", snippet)
        self.assertIn("catch", snippet)


class ThemeScriptTests(TestCase):
    def test_it_only_trusts_the_two_values_it_wrote(self):
        # localStorage is shared with anything else on the origin, so a junk
        # value must not become a data-theme attribute.
        source = JS.read_text()

        self.assertIn('value === "dark" || value === "light"', source)

    def test_both_storage_calls_are_guarded(self):
        # localStorage throws outright in private browsing on some browsers.
        # An uncaught error on the read would leave the button hidden; on the
        # write it would break the click that had just worked.
        source = JS.read_text()

        for call in ("getItem", "setItem"):
            with self.subTest(call=call):
                before = source[: source.index(call)]
                after = source[source.index(call) :]
                self.assertIn("try", before[-400:])
                self.assertIn("catch", after[:400])

    def test_it_follows_the_system_until_a_choice_is_made(self):
        source = JS.read_text()

        self.assertIn("prefers-color-scheme: dark", source)
        self.assertIn('addEventListener("change"', source)
        # It must bail out when a choice exists, or the system would override
        # the reader every time their phone switched at sunset.
        listener = source[source.index('addEventListener("change"') :]
        self.assertIn("if (stored()) return;", listener)


class BodyColourTests(TestCase):
    """Body copy must name its colour instead of inheriting the browser's.

    ``color-scheme: light dark`` tells the browser both themes exist, and it
    then picks its OWN default text colour from the *system* setting. Nothing
    on this site set a colour on body, so every paragraph took that default.
    Choosing light on a dark machine left the page white and the text white
    with it: headings were fine, because they name their colour, and the prose
    simply vanished.
    """

    def _tokens(self, block):
        return tokens_in(block)

    def test_body_names_its_own_colour(self):
        css = CSS.read_text()
        rule = css[css.index("\nbody {") : css.index("}", css.index("\nbody {"))]

        self.assertIn("color: var(--body-text)", rule)

    def test_body_text_is_defined_in_both_palettes(self):
        css = CSS.read_text()
        start = css.index(":root {")
        light = self._tokens(css[start : css.index("\n}", start)])
        media = css[css.index("@media (prefers-color-scheme: dark)") :]
        dark = self._tokens(media[media.index("{") : media.index("\n  }")])

        self.assertIn("--body-text", light)
        self.assertIn("--body-text", dark)
        self.assertNotEqual(light["--body-text"], dark["--body-text"])

    def test_body_text_contrasts_with_its_own_page(self):
        def luminance(value):
            value = value.strip().lstrip("#")
            channels = [int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)]
            adjusted = [
                c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                for c in channels
            ]
            return 0.2126 * adjusted[0] + 0.7152 * adjusted[1] + 0.0722 * adjusted[2]

        css = CSS.read_text()
        start = css.index(":root {")
        light = self._tokens(css[start : css.index("\n}", start)])
        media = css[css.index("@media (prefers-color-scheme: dark)") :]
        dark = self._tokens(media[media.index("{") : media.index("\n  }")])

        for name, palette in (("light", light), ("dark", dark)):
            with self.subTest(theme=name):
                text = luminance(palette["--body-text"])
                page = luminance(palette["--surface"])
                ratio = (max(text, page) + 0.05) / (min(text, page) + 0.05)
                self.assertGreaterEqual(ratio, 4.5)


class ColourSchemePinningTests(TestCase):
    def test_an_explicit_choice_pins_the_browser_s_own_colours(self):
        # Left at "light dark", the browser keeps styling scrollbars, form
        # controls and the overscroll area for the system setting rather than
        # the chosen one — and keeps handing out the wrong default text colour.
        css = CSS.read_text()

        self.assertIn(':root[data-theme="light"]', css)
        light_rule = css[css.index(':root[data-theme="light"] {') :]
        self.assertIn("color-scheme: light;", light_rule[: light_rule.index("}")])

        dark_rule = css[css.index(':root[data-theme="dark"] {') :]
        self.assertIn("color-scheme: dark;", dark_rule[: dark_rule.index("\n}")])
