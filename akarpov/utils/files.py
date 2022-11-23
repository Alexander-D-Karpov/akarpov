import os
from io import BytesIO

from django.contrib.auth import get_user_model
from PIL import Image


def crop_image(image_path: str, cut_to=(500, 500)):
    """Makes image's thumbnail bt given parameters. By default, crops to 500x500"""
    img = Image.open(image_path)
    blob = BytesIO()

    try:
        img.thumbnail(cut_to, Image.ANTIALIAS)
    except OSError:
        print("Can't crop")

    img.save(blob, "PNG")
    return blob


def user_file_upload_mixin(instance, filename):
    """stores user uploaded files at their folder in media dir"""
    username = ""
    if isinstance(instance, get_user_model()):
        username = instance.username
    elif hasattr(instance, "user"):
        username = instance.user.username
    elif hasattr(instance, "creator"):
        username = instance.creator.username

    return os.path.join(f"uploads/{username}/", filename)


def get_filename(filename, request):
    return filename.upper()
