import os
import re

import requests
import structlog

try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None

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
from akarpov.utils.generators import generate_charset

logger = structlog.get_logger(__name__)


def get_or_create_author(author_name):
    with transaction.atomic():
        author = Author.objects.filter(name__iexact=author_name).order_by("id").first()
        if author is not None:
            return author
        for attempt in range(5):
            try:
                slug = generate_readable_slug(author_name, Author)
                author = Author.objects.create(name=author_name, slug=slug)
                return author
            except IntegrityError:
                author = (
                    Author.objects.filter(name__iexact=author_name)
                    .order_by("id")
                    .first()
                )
                if author:
                    return author
                continue
        raise Exception(f"Failed to create or get author: {author_name}")


def get_or_create_album(album_name):
    if not album_name:
        return None
    with transaction.atomic():
        album = Album.objects.filter(name__iexact=album_name).order_by("id").first()
        if album is not None:
            return album
        for attempt in range(5):
            try:
                slug = generate_readable_slug(album_name, Album)
                album = Album.objects.create(name=album_name, slug=slug)
                return album
            except IntegrityError:
                album = (
                    Album.objects.filter(name__iexact=album_name).order_by("id").first()
                )
                if album:
                    return album
                continue
        raise Exception(f"Failed to create or get album: {album_name}")


def process_track_name(track_name: str) -> str:
    parts = track_name.split(" - ")
    processed_parts = []
    for part in parts:
        if "feat" in part:
            continue
        if "(" in part:
            part = part.split("(")[0].strip()
        processed_parts.append(part)
    return " - ".join(processed_parts)


def _safe_translate_for_filename(text: str) -> str:
    try:
        if GoogleTranslator:
            translated = GoogleTranslator(source="auto", target="en").translate(
                text,
                target_language="en",
            )
            result = slugify(translated)
            if result and len(result) > 2:
                return result
    except Exception as e:
        logger.debug("Translation failed for filename", error=str(e))
    result = slugify(text)
    return result if result else "unknown_track"


def load_track(
    path: str,
    image_path: str | None = None,
    user_id: int | None = None,
    authors: list[str] | str | None = None,
    album: str | None = None,
    name: str | None = None,
    link: str | None = None,
    **kwargs,
) -> Song | None:
    p_name = process_track_name(
        " ".join(path.split("/")[-1].split(".")[0].strip().split())
    )
    query = (
        f"{process_track_name(name) if name else p_name} "
        f"- {album if album else ''} - {', '.join(authors) if isinstance(authors, list) and authors else ''}"
    )
    search_info = search_all_platforms(query)
    orig_name = name if name else p_name

    if image_path and search_info.get("album_image", None):
        try:
            os.remove(search_info["album_image"])
        except OSError:
            pass

    if "title" in search_info and search_info["title"]:
        title = re.sub(r"\W+", "", search_info["title"]).lower()
        name_clean = re.sub(r"\W+", "", orig_name).lower()
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
    release = kwargs.get("release") or search_info.get("release", None)

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
        if isinstance(authors, str):
            authors = [authors]
        for author_name in authors:
            if not author_name or not author_name.strip():
                continue
            author = get_or_create_author(author_name.strip())
            processed_authors.append(author)
    authors = processed_authors

    existing = Song.objects.filter(
        name__iexact=name if name else p_name,
    )
    if authors:
        existing = existing.filter(authors__id__in=[x.id for x in authors])
    if album:
        existing = existing.filter(album=album)
    if existing.exists():
        song = existing.first()
        if (
            album
            and isinstance(album, Album)
            and album.authors.count() == 0
            and authors
        ):
            album.authors.set([x.id for x in authors])
        return song

    try:
        if not path.endswith(".mp3"):
            mp3_path = path.replace(path.split(".")[-1], "mp3")
            AudioSegment.from_file(path).export(mp3_path)
            os.remove(path)
            path = mp3_path
    except Exception as e:
        logger.error("Audio conversion failed", error=str(e))
        return None

    try:
        tag = MP3(path, ID3=ID3)
    except Exception as e:
        logger.error("Failed to read MP3 tags", error=str(e))
        return None

    if image_path and isinstance(image_path, str) and image_path.startswith("http"):
        try:
            response = requests.get(image_path, timeout=15)
            se = image_path.split("/")[-1]
            image_path = f'/tmp/{generate_readable_slug(name, Song)}.{"png" if "." not in se else se.split(".")[-1]}'
            with open(image_path, "wb") as f:
                f.write(response.content)
        except Exception as e:
            logger.warning("Failed to download image", error=str(e))
            image_path = None

    if image_path and isinstance(image_path, str) and os.path.exists(image_path):
        if not image_path.endswith(".png"):
            try:
                nm = image_path
                im = Image.open(image_path)
                image_path = image_path.replace(image_path.split(".")[-1], "png")
                im.save(image_path)
                os.remove(nm)
            except Exception as e:
                logger.warning("Image conversion failed", error=str(e))
                image_path = None

    song = Song(
        link=link if link else "",
        length=tag.info.length,
        name=name if name else p_name,
        album=album if isinstance(album, Album) else None,
    )

    if user_id:
        try:
            song.creator = User.objects.get(id=user_id)
        except User.DoesNotExist:
            pass

    if release:
        kwargs["release"] = release

    song.meta = {
        "explicit": kwargs.get("explicit"),
        "genre": genre,
        "lyrics": kwargs.get("lyrics"),
        "track_source": kwargs.get("track_source"),
        "release": kwargs.get("release"),
    }

    authors_text = " ".join([x.name for x in authors]) if authors else ""
    generated_name = _safe_translate_for_filename(f"{song.name} {authors_text}")
    new_file_name = generated_name + ".mp3"

    song.slug = generate_readable_slug(name if name else p_name, Song)

    for attempt in range(5):
        try:
            if (
                image_path
                and isinstance(image_path, str)
                and os.path.exists(image_path)
            ):
                with open(path, "rb") as file, open(image_path, "rb") as image:
                    song.image = File(image, name=generated_name + ".png")
                    song.file = File(file, name=new_file_name)
                    song.save()
            else:
                with open(path, "rb") as file:
                    song.file = File(file, name=new_file_name)
                    song.save()
            break
        except IntegrityError:
            song.slug = generate_readable_slug(
                song.name + "_" + generate_charset(5), Song
            )
    else:
        logger.error("Failed to save song after multiple slug attempts", name=song.name)
        return None

    if isinstance(album, Album) and not album.image and song.image:
        album.image = song.image
        album.save(update_fields=["image"])

    if authors:
        song.authors.set([x.id for x in authors])

    try:
        tag = MutagenFile(song.file.path)
        if tag is not None:
            tag["title"] = TextFrame(encoding=3, text=[name or p_name])
            if isinstance(album, Album):
                tag["album"] = TextFrame(encoding=3, text=[album.name])
            if authors:
                tag["artist"] = TextFrame(encoding=3, text=[x.name for x in authors])
            tag.save()
    except Exception as e:
        logger.warning("Failed to write mutagen tags", error=str(e))

    try:
        tag = MP3(song.file.path, ID3=ID3)
        if image_path and isinstance(image_path, str) and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                tag.tags.add(
                    APIC(
                        encoding=3,
                        mime="image/png",
                        type=3,
                        desc="Cover",
                        data=f.read(),
                    )
                )
        if release:
            tag.tags.add(TORY(text=str(release)))
        if genre:
            tag.tags.add(TCON(text=str(genre)))
        tag.save()
    except Exception as e:
        logger.warning("Failed to write ID3 tags", error=str(e))

    try:
        if os.path.exists(path):
            os.remove(path)
        if image_path and isinstance(image_path, str) and os.path.exists(image_path):
            os.remove(image_path)
    except OSError:
        pass

    return song
