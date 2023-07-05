from pathlib import Path

import mutagen
from django.core.files import File

from akarpov.music.models import Album, Author, Song, SongInQue


def load_dir(path: str):
    path = Path(path)

    for f in list(path.glob("**/*.mp3")):
        with f.open("rb") as file:
            process_mp3_file(File(file, name=str(f).split("/")[-1]), str(f))


def load_file(path: str):
    with open(path, "rb") as file:
        process_mp3_file(File(file, name=path.split("/")[-1]), path)


def process_mp3_file(file: File, path: str) -> None:
    que = SongInQue.objects.create()
    try:
        tag = mutagen.File(path, easy=True)
        que.name = tag["title"][0] if "title" in tag else path.split("/")[-1]
        que.save()
        if "artist" in tag:
            author = Author.objects.get_or_create(name=tag["artist"][0])[0]
        else:
            author = None

        if "album" in tag:
            album = Album.objects.get_or_create(name=tag["album"][0])[0]
        else:
            album = None

        song, created = Song.objects.get_or_create(
            name=tag["title"][0] if "title" in tag else path.split("/")[-1],
            author=author,
            album=album,
        )
        song.file = file
        song.save(update_fields=["file"])
        que.delete()
    except Exception as e:
        que.name = e
        que.error = True
        que.save()
