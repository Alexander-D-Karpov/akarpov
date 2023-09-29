import os

from django.core.files import File
from mutagen import File as MutagenFile
from mutagen.id3 import APIC, ID3, TCON, TORY, TextFrame
from mutagen.mp3 import MP3
from PIL import Image
from pydub import AudioSegment

from akarpov.music.models import Album, Author, Song


def load_track(
    path: str,
    image_path: str | None = None,
    user_id: int | None = None,
    authors: list[str] | str | None = None,
    album: str | None = None,
    name: str | None = None,
    link: str | None = None,
    **kwargs,
) -> Song:
    p_name = path.split("/")[-1]

    if album and type(album) is str and album.startswith("['"):
        album = album.replace("['", "").replace("']", "")

    if authors:
        authors = [Author.objects.get_or_create(name=x)[0] for x in authors if authors]
    else:
        authors = []
    if album:
        if type(album) is str:
            album = Album.objects.get_or_create(name=album)[0]
        elif type(album) is list:
            album = Album.objects.get_or_create(name=album[0])[0]
    else:
        album = None

    if sng := Song.objects.filter(
        name=name if name else p_name,
        authors__id__in=[x.id for x in authors],
        album=album,
    ):
        return sng.first()

    if not path.endswith(".mp3"):
        mp3_path = path.replace(path.split(".")[-1], "mp3")
        AudioSegment.from_file(path).export(mp3_path)
        os.remove(path)
        path = mp3_path

    tag = MP3(path, ID3=ID3)
    if image_path:
        if not image_path.endswith(".png"):
            nm = image_path
            im = Image.open(image_path)
            image_path = image_path.replace(image_path.split(".")[-1], "png")
            im.save(image_path)
            os.remove(nm)

    song = Song(
        link=link if link else "",
        length=tag.info.length,
        name=name if name else p_name,
        album=album,
    )

    if user_id:
        song.user_id = user_id

    if kwargs:
        song.meta = kwargs

    if image_path:
        with open(path, "rb") as file, open(image_path, "rb") as image:
            song.image = File(image, name=image_path.split("/")[-1])
            song.file = File(file, name=path.split("/")[-1])
            song.save()
    else:
        with open(path, "rb") as file:
            song.file = File(file, name=path.split("/")[-1])
            song.save()

    if authors:
        song.authors.set(authors)

    # set music meta
    tag = MutagenFile(song.file.path)
    tag["title"] = TextFrame(encoding=3, text=[name])
    if album:
        tag["album"] = TextFrame(encoding=3, text=[album.name])
    if authors:
        tag["artist"] = TextFrame(encoding=3, text=[x.name for x in authors])
    tag.save()

    tag = MP3(song.file.path, ID3=ID3)
    if image_path:
        with open(image_path, "rb") as f:
            tag.tags.add(
                APIC(
                    encoding=3,  # 3 is for utf-8
                    mime="image/png",  # image/jpeg or image/png
                    type=3,  # 3 is for the cover image
                    desc="Cover",
                    data=f.read(),
                )
            )
    if "release" in kwargs:
        tag.tags.add(TORY(text=kwargs["release"]))
    if "genre" in kwargs:
        tag.tags.add(TCON(text=kwargs["genre"]))
    tag.save()

    if os.path.exists(path):
        os.remove(path)

    if os.path.exists(image_path):
        os.remove(image_path)

    return song
