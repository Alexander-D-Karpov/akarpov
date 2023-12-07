from django.test import TestCase

from akarpov.users.forms import UserAdminCreationForm


class UserFormTest(TestCase):
    def test_valid_form(self):
        form = UserAdminCreationForm(
            data={
                "username": "testuser",
                "password1": "P4sSw0rD!",
                "password2": "P4sSw0rD!",
            }
        )
        self.assertTrue(form.is_valid())

    def test_insecure_password(self):
        form = UserAdminCreationForm(
            data={
                "username": "testuser",
                "password1": "password",
                "password2": "password",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(
            form.errors["password2"],
            ["This password is too common."],
        )

    def test_invalid_form(self):
        form = UserAdminCreationForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 3)
        self.assertEqual(form.errors["username"], ["This field is required."])
