import os

from django.conf import settings

from akarpov.utils.generators import generate_charset


def user_unique_file_upload(instance, filename):
    """stores user uploaded files at their folder with unique file name"""
    username = instance.user.username
    path = os.path.join(settings.MEDIA_ROOT, f"files/{username}/")
    slug = generate_charset(5)
    while os.path.isdir(path + slug):
        slug = generate_charset(5)

    return os.path.join(f"files/{username}/{slug}", filename)
