import os
import re

from deep_translator import GoogleTranslator
from django.core.files import File
from django.db import transaction
from django.utils.text import slugify
from mutagen import File as MutagenFile
from mutagen.id3 import APIC, ID3, TCON, TORY, TextFrame
from mutagen.mp3 import MP3
from PIL import Image
from pydub import AudioSegment

from akarpov.music.models import Album, Author, Song
from akarpov.music.services.info import generate_readable_slug, search_all_platforms
from akarpov.users.models import User


def process_track_name(track_name: str) -> str:
    # Split the track name by dash and parentheses
    parts = track_name.split(" - ")
    processed_parts = []

    for part in parts:
        if "feat" in part:
            continue
        if "(" in part:
            part = part.split("(")[0].strip()
        processed_parts.append(part)

    processed_track_name = " - ".join(processed_parts)
    return processed_track_name


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
    p_name = process_track_name(
        " ".join(path.split("/")[-1].split(".")[0].strip().split())
    )
    query = (
        f"{process_track_name(name) if name else p_name} "
        f"- {album if album else ''} - {', '.join(authors) if authors else ''}"
    )
    search_info = search_all_platforms(query)
    orig_name = name if name else p_name

    if image_path and search_info.get("album_image", None):
        os.remove(search_info["album_image"])
    if "title" in search_info:
        title = re.sub(r"\W+", "", search_info["title"]).lower()
        name_clean = re.sub(r"\W+", "", name).lower()

        # Check if title is in name
        if title in name_clean:
            name = search_info["title"]
        else:
            name = process_track_name(" ".join(p_name.strip().split("-")))

    if not name:
        name = orig_name

    album = album or search_info.get("album_name", None)
    authors = authors or search_info.get("artists", [])
    genre = kwargs.get("genre") or search_info.get("genre", None)
    image_path = image_path or search_info.get("album_image", "")
    release = (
        kwargs["release"] if "release" in kwargs else search_info.get("release", None)
    )

    if album and type(album) is str and album.startswith("['"):
        album = album.replace("['", "").replace("']", "")

    re_authors = []
    if authors:
        for x in authors:
            while True:
                try:
                    with transaction.atomic():
                        author, created = Author.objects.get_or_create(
                            name__iexact=x, defaults={"name": x}
                        )
                    re_authors.append(author)
                    break
                except Author.MultipleObjectsReturned:
                    # If multiple authors are found, delete all but one
                    Author.objects.filter(name__iexact=x).exclude(
                        id=Author.objects.filter(name__iexact=x).first().id
                    ).delete()
    authors = re_authors

    if album:
        if type(album) is str:
            album_name = album
        elif type(album) is list:
            album_name = album[0]
        else:
            album_name = None
        if album_name:
            album, created = Album.objects.get_or_create(
                name__iexact=album_name, defaults={"name": album_name}
            )

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
        song.creator = User.objects.get(id=user_id)

    if release:
        kwargs["release"] = release

    kwargs = {
        "explicit": kwargs["explicit"] if "explicit" in kwargs else None,
        "genre": genre,
        "lyrics": kwargs["lyrics"] if "lyrics" in kwargs else None,
        "track_source": kwargs["track_source"] if "track_source" in kwargs else None,
    } | kwargs

    song.meta = kwargs

    generated_name = str(
        slugify(
            GoogleTranslator(source="auto", target="en").translate(
                f"{song.name} {' '.join([x.name for x in authors])}",
                target_language="en",
            )
        )
    )

    new_file_name = generated_name + ".mp3"

    if image_path:
        with open(path, "rb") as file, open(image_path, "rb") as image:
            song.image = File(image, name=generated_name + ".png")
            song.file = File(file, name=new_file_name)
            song.save()
    else:
        with open(path, "rb") as file:
            song.file = File(file, name=new_file_name)
            song.save()

    if not album.image and song.image:
        album.image = song.image
        album.save()

    if authors:
        song.authors.set([x.id for x in authors])

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
    if release:
        tag.tags.add(TORY(text=kwargs["release"]))
    if genre:
        tag.tags.add(TCON(text=kwargs["genre"]))
    tag.save()

    if os.path.exists(path):
        os.remove(path)

    if os.path.exists(image_path):
        os.remove(image_path)

    song.slug = generate_readable_slug(song.name, Song)
    song.save()

    return song
