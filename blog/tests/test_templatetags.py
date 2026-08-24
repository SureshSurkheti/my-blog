from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase

from blog.templatetags.blog_extras import query_replace, reading_time, render_markdown


class MarkdownFilterTests(SimpleTestCase):
    def test_renders_basic_markdown(self):
        self.assertIn("<strong>bold</strong>", render_markdown("some **bold** text"))
        self.assertIn("<h2", render_markdown("## A heading"))
        self.assertIn("<li>", render_markdown("- one\n- two"))

    def test_renders_fenced_code_blocks(self):
        html = render_markdown("```\nprint('hi')\n```")
        self.assertIn("<pre", html)
        self.assertIn("print('hi')", html)

    def test_strips_script_tags(self):
        html = render_markdown("Hello <script>alert('xss')</script> world")
        self.assertNotIn("<script>", html)
        self.assertNotIn("alert", html)

    def test_strips_event_handler_attributes(self):
        html = render_markdown('<img src="x.png" onerror="alert(1)" alt="x">')
        self.assertNotIn("onerror", html)

    def test_strips_javascript_urls(self):
        html = render_markdown('<a href="javascript:alert(1)">click</a>')
        self.assertNotIn("javascript:", html)

    def test_keeps_safe_links_and_images(self):
        html = render_markdown("[docs](https://example.com) ![a cat](/img.png)")
        self.assertIn('href="https://example.com"', html)
        self.assertIn('alt="a cat"', html)
        self.assertIn('src="/img.png"', html)

    def test_empty_input(self):
        self.assertEqual(render_markdown(""), "")
        self.assertEqual(render_markdown(None), "")


class ReadingTimeTests(SimpleTestCase):
    def test_short_text_is_at_least_one_minute(self):
        self.assertEqual(reading_time("just a few words"), 1)

    def test_scales_with_length(self):
        self.assertEqual(reading_time(" ".join(["word"] * 600)), 3)

    def test_handles_empty_input(self):
        self.assertEqual(reading_time(""), 1)
        self.assertEqual(reading_time(None), 1)


class QueryReplaceTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _context(self, path):
        return {"request": self.factory.get(path)}

    def test_preserves_other_parameters(self):
        result = query_replace(self._context("/search?q=django&page=1"), page=2)
        self.assertIn("q=django", result)
        self.assertIn("page=2", result)
        self.assertNotIn("page=1", result)

    def test_adds_a_parameter_when_absent(self):
        self.assertEqual(query_replace(self._context("/posts"), page=3), "page=3")

    def test_none_removes_a_parameter(self):
        result = query_replace(self._context("/search?q=x&page=4"), page=None)
        self.assertEqual(result, "q=x")

    def test_usable_from_a_template(self):
        template = Template("{% load blog_extras %}{% query_replace page=2 %}")
        rendered = template.render(
            Context({"request": self.factory.get("/posts?q=hi")})
        )
        self.assertIn("q=hi", rendered)
        self.assertIn("page=2", rendered)


class SyntaxHighlightingTests(SimpleTestCase):
    """Pygments output has to survive the HTML sanitizer to be any use."""

    def test_fenced_python_is_highlighted(self):
        html = render_markdown("```python\ndef greet():\n    return 1\n```")

        self.assertIn('class="codehilite"', html)
        self.assertIn("<span", html)  # tokens survived nh3
        self.assertIn("greet", html)

    def test_unknown_language_still_renders_the_code(self):
        html = render_markdown("```notalanguage\nsome text\n```")
        self.assertIn("some text", html)

    def test_inline_code_is_left_alone(self):
        html = render_markdown("use the `manage.py` command")
        self.assertIn("<code>manage.py</code>", html)
