import os

from django.core.files import File
from mutagen.mp3 import MP3
from PIL import Image
from pydub import AudioSegment

from akarpov.music.models import Album, Author, Song


def load_track(
    path: str,
    image_path: str | None = None,
    authors: list[str] | str | None = None,
    album: str | None = None,
    name: str | None = None,
    link: str | None = None,
) -> Song:
    p_name = path.split("/")[-1]
    if authors:
        authors = [Author.objects.get_or_create(name=x)[0] for x in authors]
    else:
        authors = []
    if album:
        album = Album.objects.get_or_create(name=album)[0]
    else:
        album = None

    if sng := Song.objects.filter(
        name=name if name else p_name, authors=authors, album=album
    ):
        return sng.first()

    if not path.endswith(".mp3"):
        mp3_path = path.replace(path.split(".")[-1], "mp3")
        AudioSegment.from_file(path).export(mp3_path)
        os.remove(path)
        path = mp3_path

    audio = MP3(path)

    if image_path:
        if not image_path.endswith(".png"):
            im = Image.open(image_path)
            image_path = image_path.replace(image_path.split(".")[-1], "png")
            im.save(image_path)

    song = Song(
        link=link, length=audio.info.length, name=name if name else p_name, album=album
    )

    with open(path, "rb") as file:
        song.file = File(file, name=path.split("/")[-1])

    if image_path:
        with open(image_path, "rb") as file:
            song.image = File(file, name=image_path.split("/")[-1])

    if authors:
        song.authors.set(authors)

    song.save()
    return song
