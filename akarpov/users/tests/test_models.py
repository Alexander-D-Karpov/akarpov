import pytest

pytestmark = pytest.mark.django_db


class TestUser:
    @pytest.fixture
    def user_with_code(self, user_factory):
        return user_factory(user_code="1234")

    def test_send_code(self, mailoutbox, user_factory):
        user_with_code.send_code()

        assert len(mailoutbox) == 1
        m = mailoutbox[0]
        assert list(m.to) == [user_with_code.email]
        assert "1234" in m.body
