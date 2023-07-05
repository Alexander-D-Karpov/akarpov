import os
from io import BytesIO

from django.contrib.auth import get_user_model
from PIL import Image


def crop_image(image_path: str, length: int = 500):
    """Makes image's thumbnail bt given parameters. By default, crops to 500x500"""
    image = Image.open(image_path)
    blob = BytesIO()

    try:
        if image.size[0] < image.size[1]:
            # The image is in portrait mode. Height is bigger than width.

            # This makes the width fit the LENGTH in pixels while conserving the ration.
            resized_image = image.resize(
                (length, int(image.size[1] * (length / image.size[0])))
            )

            # Amount of pixel to lose in total on the height of the image.
            required_loss = resized_image.size[1] - length

            # Crop the height of the image so as to keep the center part.
            resized_image = resized_image.crop(
                box=(
                    0,
                    int(required_loss / 2),
                    length,
                    int(resized_image.size[1] - required_loss / 2),
                )
            )
        else:
            # This image is in landscape mode or already squared. The width is bigger than the heihgt.

            # This makes the height fit the LENGTH in pixels while conserving the ration.
            resized_image = image.resize(
                (int(image.size[0] * (length / image.size[1])), length)
            )

            # Amount of pixel to lose in total on the width of the image.
            required_loss = resized_image.size[0] - length

            # Crop the width of the image so as to keep 1080 pixels of the center part.
            resized_image = resized_image.crop(
                box=(
                    int(required_loss / 2),
                    0,
                    int(resized_image.size[0] - required_loss / 2),
                    length,
                )
            )
        resized_image.save(blob, "PNG")
    except OSError:
        print("Can't crop")
    return blob


def user_file_upload_mixin(instance, filename):
    """stores user uploaded files at their folder in media dir"""
    username = ""
    if isinstance(instance, get_user_model()):
        username = instance.username + "/"
    elif hasattr(instance, "user"):
        username = instance.user.username + "/"
    elif hasattr(instance, "creator"):
        username = instance.creator.username + "/"

    return os.path.join(f"uploads/{username}", filename)
