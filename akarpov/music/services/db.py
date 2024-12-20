import os
import re

import requests

try:
    from deep_translator import GoogleTranslator  # TODO: move to another service
except requests.exceptions.JSONDecodeError:
    print("Failed to initialize GoogleTranslator due to external API issues.")
from django.core.files import File
from django.db import IntegrityError, transaction
from django.utils.text import slugify
from mutagen import File as MutagenFile
from mutagen.id3 import APIC, ID3, TCON, TORY, TextFrame
from mutagen.mp3 import MP3
from PIL import Image
from pydub import AudioSegment

from akarpov.music.models import Album, Author, Song
from akarpov.music.services.info import generate_readable_slug, search_all_platforms
from akarpov.users.models import User
from akarpov.utils.generators import generate_charset  # Import generate_charset


def get_or_create_author(author_name):
    """Get or create author with unique slug."""
    with transaction.atomic():
        author = Author.objects.filter(name__iexact=author_name).order_by("id").first()
        if author is None:
            for attempt in range(5):
                try:
                    slug = generate_readable_slug(author_name, Author)
                    author = Author.objects.create(name=author_name, slug=slug)
                    return author
                except IntegrityError:
                    # Slug conflict, retry slug generation
                    continue
            else:
                # If we still fail, get the existing author
                author = (
                    Author.objects.filter(name__iexact=author_name)
                    .order_by("id")
                    .first()
                )
                if author:
                    return author
                else:
                    raise Exception("Failed to create or get author")
        else:
            return author


def get_or_create_album(album_name):
    """Get or create album with unique slug."""
    if not album_name:
        return None

    with transaction.atomic():
        album = Album.objects.filter(name__iexact=album_name).order_by("id").first()
        if album is None:
            for attempt in range(5):
                try:
                    slug = generate_readable_slug(album_name, Album)
                    album = Album.objects.create(name=album_name, slug=slug)
                    return album
                except IntegrityError:
                    # Slug conflict, retry slug generation
                    continue
            else:
                # If we still fail, get the existing album
                album = (
                    Album.objects.filter(name__iexact=album_name).order_by("id").first()
                )
                if album:
                    return album
                else:
                    raise Exception("Failed to create or get album")
        else:
            return album


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
        name_clean = re.sub(r"\W+", "", orig_name).lower()

        # Check if title is in name
        if title in name_clean:
            name = search_info["title"]
        elif not name:
            name = process_track_name(" ".join(p_name.strip().split("-")))
            clear_name = [
                "(Official HD Video)",
                "(Official Music Video)",
                "(Official Video)",
                "Official Video",
                "Official Music Video",
                "Official HD Video",
            ]
            for c in clear_name:
                name = name.replace(c, "")

    if not name:
        name = orig_name

    album = album or search_info.get("album_name", None)
    authors = authors or search_info.get("artists", [])
    genre = kwargs.get("genre") or search_info.get("genre", None)
    image_path = image_path or search_info.get("album_image", "")
    release = (
        kwargs["release"] if "release" in kwargs else search_info.get("release", None)
    )

    if album and isinstance(album, str) and album.startswith("['"):
        album = album.replace("['", "").replace("']", "")

    if album:
        if isinstance(album, str):
            album_name = album
        elif isinstance(album, list):
            album_name = album[0]
        else:
            album_name = None
        if album_name:
            album = get_or_create_album(album_name)

    processed_authors = []
    if authors:
        for author_name in authors:
            author = get_or_create_author(author_name)
            processed_authors.append(author)
    authors = processed_authors

    if sng := Song.objects.filter(
        name__iexact=name if name else p_name,
        authors__id__in=[x.id for x in authors],
        album=album,
    ):
        return sng.first()
    try:
        if not path.endswith(".mp3"):
            mp3_path = path.replace(path.split(".")[-1], "mp3")
            AudioSegment.from_file(path).export(mp3_path)
            os.remove(path)
            path = mp3_path
    except Exception as e:
        print(e)
        return Song.objects.none()

    tag = MP3(path, ID3=ID3)

    if image_path and image_path.startswith("http"):
        response = requests.get(image_path)
        se = image_path.split("/")[-1]
        image_path = f'/tmp/{generate_readable_slug(name, Song)}.{"png" if "." not in se else se.split(".")[-1]}'
        with open(image_path, "wb") as f:
            f.write(response.content)

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

    # Generate unique slug for the song
    song.slug = generate_readable_slug(name if name else p_name, Song)

    # Try to save the song, handling potential slug conflicts
    for attempt in range(5):
        try:
            if image_path:
                with open(path, "rb") as file, open(image_path, "rb") as image:
                    song.image = File(image, name=generated_name + ".png")
                    song.file = File(file, name=new_file_name)
                    song.save()
            else:
                with open(path, "rb") as file:
                    song.file = File(file, name=new_file_name)
                    song.save()
            break  # Successfully saved the song
        except IntegrityError:
            # Slug conflict, generate a new slug using generate_charset
            song.slug = generate_readable_slug(
                song.name + "_" + generate_charset(5), Song
            )
    else:
        raise Exception("Failed to save song with unique slug after multiple attempts")

    if not album.image and song.image:
        album.image = song.image
        album.save()

    if authors:
        song.authors.set([x.id for x in authors])

    # Set music metadata
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

    return song
