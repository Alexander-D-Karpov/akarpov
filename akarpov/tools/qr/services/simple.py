import os

from amzqr import amzqr
from django.core.files import File

from akarpov.tools.qr.models import QR
from akarpov.users.models import User
from akarpov.utils.generators import generate_charset


def run(words: str, path: str = "/tmp/", user: User = None) -> QR:
    version, level, qr_name = amzqr.run(
        words,
        version=1,
        level="H",
        picture=None,
        colorized=False,
        contrast=1.0,
        brightness=1.0,
        save_name=generate_charset(4) + ".png",
        save_dir=path,
    )
    qr = QR(body=words)
    if user:
        qr.user = user

    path = qr_name
    with open(path, "rb") as f:
        qr.image.save(
            qr_name.split("/")[-1],
            File(f),
            save=False,
        )
    os.remove(path)
    return qr
