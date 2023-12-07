from django.test import Client, TestCase
from django.urls import reverse

from akarpov.users.tests.factories import UserFactory


class UserViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()

    def test_user_detail_view(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("users:detail", kwargs={"username": self.user.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)
