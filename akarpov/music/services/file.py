import os
from io import BytesIO
from pathlib import Path
from random import randint

import mutagen
from mutagen.id3 import ID3
from PIL import Image, UnidentifiedImageError

from akarpov.music.models import Song
from akarpov.music.services.db import load_track


def load_dir(path: str):
    path = Path(path)

    for f in list(path.glob("**/*.mp3")):
        process_mp3_file(str(f))


def load_file(path: str):
    process_mp3_file(path)


def process_mp3_file(path: str) -> None:
    tag = mutagen.File(path, easy=True)
    if "artist" in tag:
        author = tag["artist"]
    else:
        author = None

    if "album" in tag:
        album = tag["album"]
    else:
        album = None
    name = tag["title"][0] if "title" in tag else path.split("/")[-1]
    f = Song.objects.filter(name=name)
    if author:
        f.filter(authors__name__in=author)
    if album:
        f.filter(album__name=album)
    if f.exists():
        return

    tags = ID3(path)
    pict = [x for x in tags.getall("APIC") if x]
    image_pth = None
    if pict:
        try:
            pict = pict[0].data
            im = Image.open(BytesIO(pict))
            image_pth = f"/tmp/{randint(1, 1000000)}.png"
            if os.path.exists(image_pth):
                image_pth = f"/tmp/{randint(1, 1000000)}.png"
            im.save(image_pth)
        except UnidentifiedImageError:
            pass
    load_track(path, image_pth, author, album, name)
    if image_pth and os.path.exists(image_pth):
        os.remove(image_pth)
