from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from blog.models import Post

from .factories import make_author, make_comment, make_post, make_tag


class AdminSmokeTests(TestCase):
    def setUp(self):
        User.objects.create_superuser("root", "root@example.com", "pw12345!")
        self.client.login(username="root", password="pw12345!")

    def test_changelists_load(self):
        author = make_author()
        post = make_post(author=author, tags=[make_tag("Django")])
        make_comment(post)

        for model in ("post", "author", "tag", "comment"):
            with self.subTest(model=model):
                response = self.client.get(reverse(f"admin:blog_{model}_changelist"))
                self.assertEqual(response.status_code, 200)

    def test_publish_action_stamps_the_date(self):
        draft = make_post("Draft copy", published=False)

        self.client.post(
            reverse("admin:blog_post_changelist"),
            {"action": "publish_selected", "_selected_action": [draft.pk]},
            follow=True,
        )

        draft.refresh_from_db()
        self.assertEqual(draft.status, Post.Status.PUBLISHED)
        self.assertIsNotNone(draft.published_at)

    def test_unpublish_action_moves_back_to_draft(self):
        post = make_post("Live one")

        self.client.post(
            reverse("admin:blog_post_changelist"),
            {"action": "unpublish_selected", "_selected_action": [post.pk]},
            follow=True,
        )

        post.refresh_from_db()
        self.assertEqual(post.status, Post.Status.DRAFT)
