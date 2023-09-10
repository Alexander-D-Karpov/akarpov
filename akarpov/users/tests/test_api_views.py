from django.urls import reverse_lazy
from pytest_lambda import lambda_fixture, static_fixture
from rest_framework import status


class TestChangePassword:
    url = static_fixture(reverse_lazy("api:users:password"))
    new_password = static_fixture("P@ssw0rd123")
    user = lambda_fixture(lambda user_factory: user_factory(password="P@ssw0rd"))

    def test_ok(self, api_user_client, url, new_password, user):
        response = api_user_client.put(
            url, {"old_password": "P@ssw0rd", "password": new_password}
        )

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password(new_password)

    def test_return_err_if_data_is_invalid(
        self, api_user_client, url, new_password, user
    ):
        response = api_user_client.put(
            url, {"old_password": "123456", "password": new_password}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert not user.check_password(new_password)
