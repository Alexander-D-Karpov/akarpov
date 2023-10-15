import pytest
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


class TestUserListRetrieve:
    url = static_fixture(reverse_lazy("api:users:list"))
    url_retrieve = static_fixture(
        reverse_lazy("api:users:get", kwargs={"username": "TestUser"})
    )
    user = lambda_fixture(
        lambda user_factory: user_factory(password="P@ssw0rd", username="TestUser")
    )

    def test_user_list_site_users(self, api_user_client, url, user):
        response = api_user_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1
        assert response.json()["results"][0]["username"] == user.username

    def test_user_retrieve_by_username(self, api_user_client, url_retrieve, user):
        response = api_user_client.get(url_retrieve)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == user.username
        assert response.json()["id"] == user.id

    def test_user_retrieve_by_id(self, api_user_client, user):
        response = api_user_client.get(
            reverse_lazy("api:users:get_by_id", kwargs={"pk": user.id})
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == user.username
        assert response.json()["id"] == user.id


class TestUserSelfRetrieve:
    url = static_fixture(reverse_lazy("api:users:self"))
    user = lambda_fixture(lambda user_factory: user_factory(password="P@ssw0rd"))

    def test_user_self_retrieve(self, api_user_client, url, user):
        response = api_user_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == user.username
        assert response.json()["id"] == user.id

    def test_user_self_update_put(self, api_user_client, url, user):
        response = api_user_client.put(url, {"username": "NewUsername"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == "NewUsername"
        assert response.json()["id"] == user.id
        user.refresh_from_db()
        assert user.username == "NewUsername"

    def test_user_self_update_patch(self, api_user_client, url, user):
        response = api_user_client.patch(url, {"username": "NewUsername"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == "NewUsername"
        assert response.json()["id"] == user.id
        user.refresh_from_db()
        assert user.username == "NewUsername"

    def test_user_self_delete(self, api_user_client, url, user):
        response = api_user_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b""
        with pytest.raises(user.DoesNotExist):
            user.refresh_from_db()
