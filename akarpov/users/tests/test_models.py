from akarpov.files.consts import USER_INITIAL_FILE_UPLOAD
from akarpov.users.models import User


def test_user_creation(user_factory):
    user = user_factory(username="testuser", email="test@example.com")
    assert isinstance(user, User)
    assert user.__str__() == user.username


def test_user_create(user_factory):
    user = user_factory()
    password = "123"
    user.set_password(password)
    assert user.check_password(password)


def test_auto_file_upload_size(user_factory):
    user = user_factory()
    size = USER_INITIAL_FILE_UPLOAD
    assert user.left_file_upload == size


def test_user_image_create(user_factory):
    user = user_factory()
    assert user.image
