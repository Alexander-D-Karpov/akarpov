from akarpov.users.models import User


def test_user_create(user: User):
    password = "123"
    user.set_password(password)
    assert user.check_password(password)
