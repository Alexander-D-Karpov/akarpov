import os
import time
from io import BytesIO
from pathlib import Path
from random import randint

import librosa
import mutagen
import numpy as np
from django.core.files import File
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils.text import slugify
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from PIL import Image, UnidentifiedImageError

from akarpov.music.models import Album, Author, Song
from akarpov.music.services.db import load_track
from akarpov.users.models import User
from akarpov.utils.generators import generate_charset


def load_dir(path: str, user_id: int):
    path = Path(path)

    for f in list(path.glob("**/*.mp3")):
        process_mp3_file(str(f), user_id=user_id)


def load_file(path: str, user_id: int):
    # TODO: convert to mp3 if not mp3
    process_mp3_file(path, user_id)


def process_mp3_file(path: str, user_id: int) -> None:
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
    load_track(path, image_pth, user_id, author, album, name)
    if image_pth and os.path.exists(image_pth):
        os.remove(image_pth)


def analyze_music_loudness(mp3_file):
    y, sr = librosa.load(mp3_file, sr=None)
    frame_length = int(0.1 * sr)
    stft = np.abs(librosa.stft(y, n_fft=frame_length, hop_length=frame_length))
    rms_energy = librosa.feature.rms(
        S=stft, frame_length=frame_length, hop_length=frame_length
    )[0]
    scaling_factor = 10000
    scaled_rms_energy = rms_energy * scaling_factor

    # Convert the scaled RMS energy to a list of integers
    rms_energy_integers = [int(x) for x in scaled_rms_energy]

    return rms_energy_integers


def set_song_volume(song: Song):
    mp3_file = song.file.path
    song.volume = analyze_music_loudness(mp3_file)
    song.save(update_fields=["volume"])


BATCH_SIZE = 10
BATCH_CHECK_DELAY = 10  # seconds


class FileProcessor:
    def __init__(self):
        self.failed_files: list[str] = []
        self.processed_files: set[str] = set()
        self.current_batch: dict[str, dict] = {}

    def load_dir(self, path: str, user_id: int) -> tuple[list[str], int]:
        path = Path(path)
        files = list(path.glob("**/*.mp3"))
        total_files = len(files)

        for i in range(0, len(files), BATCH_SIZE):
            batch = files[i : i + BATCH_SIZE]  # noqa
            self._process_batch(batch, user_id)

            # Wait and verify batch
            time.sleep(BATCH_CHECK_DELAY)
            self._verify_batch()

            print(
                "Batch processed",
                processed=len(self.processed_files),
                failed=len(self.failed_files),
                total=total_files,
                remaining=total_files
                - len(self.processed_files)
                - len(self.failed_files),
            )

        return self.failed_files, len(self.processed_files)

    def _process_batch(self, files: list[Path], user_id: int):
        self.current_batch.clear()

        for file_path in files:
            file_str = str(file_path)
            if file_str in self.processed_files or file_str in self.failed_files:
                continue

            try:
                file_info = self._extract_file_info(file_str)
                if self._check_exists(file_info):
                    self.processed_files.add(file_str)
                    continue

                self.current_batch[file_str] = file_info
                self._process_file(file_str, file_info, user_id)

            except Exception as e:
                print("File processing failed", file=file_str, error=str(e))
                self.failed_files.append(file_str)

    def _verify_batch(self):
        for file_path, info in self.current_batch.items():
            if not self._verify_file(file_path, info):
                print("File verification failed", file=file_path)
                self.failed_files.append(file_path)
            else:
                self.processed_files.add(file_path)

    def _extract_file_info(self, path: str) -> dict:
        tag = mutagen.File(path, easy=True)
        return {
            "author": tag.get("artist"),
            "album": tag.get("album"),
            "name": tag.get("title", [path.split("/")[-1]])[0],
            "image": self._extract_image(path),
        }

    def _extract_image(self, path: str) -> str | None:
        try:
            tags = ID3(path)
            pict = [x for x in tags.getall("APIC") if x]
            if not pict:
                return None

            pict_data = pict[0].data
            im = Image.open(BytesIO(pict_data))
            image_path = f"/tmp/{randint(1, 1000000)}.png"
            while os.path.exists(image_path):
                image_path = f"/tmp/{randint(1, 1000000)}.png"
            im.save(image_path)
            return image_path
        except (UnidentifiedImageError, Exception) as e:
            print("Image extraction failed", error=str(e))
            return None

    def _check_exists(self, info: dict) -> bool:
        query = Song.objects.filter(name=info["name"])
        if info["author"]:
            query = query.filter(authors__name__in=info["author"])
        if info["album"]:
            query = query.filter(album__name=info["album"])
        return query.exists()

    def _verify_file(self, file_path: str, info: dict) -> bool:
        song = Song.objects.filter(name=info["name"], file__isnull=False).first()

        if not song:
            return False

        # Verify file exists and is readable
        if not os.path.exists(song.file.path):
            return False

        # Verify image if it was expected
        if info["image"] and not song.image:
            return False

        # Verify metadata
        if info["author"]:
            if not song.authors.filter(name__in=info["author"]).exists():
                return False
        if info["album"]:
            if not song.album or song.album.name != info["album"]:
                return False

        return True

    def _process_file(self, path: str, info: dict, user_id: int):
        try:
            song = load_track(
                path=path,
                image_path=info["image"],
                user_id=user_id,
                authors=info["author"],
                album=info["album"],
                name=info["name"],
            )
            if info["image"] and os.path.exists(info["image"]):
                os.remove(info["image"])

            set_song_volume(song)

        except Exception as e:
            print("File processing failed", file=path, error=str(e))
            self.failed_files.append(path)


def clean_title_for_slug(title: str) -> str:
    """Clean title for slug generation."""
    # Remove common suffixes
    suffixes = [
        "(Original Mix)",
        "(Radio Edit)",
        "(Extended Mix)",
        "(Official Video)",
        "(Music Video)",
        "(Lyric Video)",
        "(Audio)",
        "(Official Audio)",
        "(Visualizer)",
        "(Official Music Video)",
        "(Official Lyric Video)",
    ]
    cleaned = title
    for suffix in suffixes:
        cleaned = cleaned.replace(suffix, "")
    return cleaned.strip()


def process_authors_string(authors_str: str) -> list[str]:
    """Split author string into individual author names."""
    if not authors_str:
        return []

    # First split by major separators
    authors = []
    for part in authors_str.split("/"):
        for subpart in part.split("&"):
            # Handle various featuring cases
            for feat_marker in [
                " feat.",
                " ft.",
                " featuring.",
                " presents ",
                " pres. ",
            ]:
                if feat_marker in subpart.lower():
                    parts = subpart.lower().split(feat_marker, 1)
                    authors.extend(part.strip() for part in parts)
                    break
            else:
                # Handle collaboration markers
                if " x " in subpart:
                    authors.extend(p.strip() for p in subpart.split(" x "))
                else:
                    authors.append(subpart.strip())

    # Remove duplicates while preserving order
    seen = set()
    return [x for x in authors if not (x.lower() in seen or seen.add(x.lower()))]


def extract_mp3_metadata(file_path: str) -> dict | None:
    """Extract metadata from MP3 file."""
    try:
        audio = MP3(file_path, ID3=ID3)
        tags = audio.tags if audio.tags else {}

        # Get filename without extension for fallback
        base_filename = os.path.splitext(os.path.basename(file_path))[0]

        metadata = {
            "title": None,
            "album": None,
            "artists": None,
            "genre": None,
            "release_year": None,
            "length": audio.info.length,
            "image_data": None,
            "image_mime": None,
        }

        if tags:
            # Extract basic metadata with fallbacks
            metadata["title"] = str(tags.get("TIT2", "")) or base_filename
            metadata["album"] = str(tags.get("TALB", ""))
            metadata["artists"] = str(tags.get("TPE1", "")) or str(tags.get("TPE2", ""))
            metadata["genre"] = str(tags.get("TCON", ""))
            metadata["release_year"] = str(tags.get("TDRC", "")) or str(
                tags.get("TYER", "")
            )

            # Extract cover art
            for tag in tags.getall("APIC"):
                if tag.type == 3:  # Front cover
                    metadata["image_data"] = tag.data
                    metadata["image_mime"] = tag.mime
                    break

            # Clean up title if it came from filename
            if metadata["title"] == base_filename:
                parts = base_filename.split(" - ", 1)
                if len(parts) > 1 and not metadata["artists"]:
                    metadata["artists"] = parts[0]
                    metadata["title"] = parts[1]

        return metadata
    except Exception as e:
        print(f"Error extracting metadata from {file_path}: {str(e)}")
        return None


def generate_unique_slug(
    base_name: str, model_class, existing_id=None, max_length=20
) -> str:
    """Generate a unique slug for a model instance."""
    # Clean and slugify the base name
    slug = slugify(clean_title_for_slug(base_name))

    # Truncate if necessary
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit("-", 1)[0]

    original_slug = slug
    counter = 1

    # Check for uniqueness
    while True:
        if existing_id:
            exists = (
                model_class.objects.filter(slug=slug).exclude(id=existing_id).exists()
            )
        else:
            exists = model_class.objects.filter(slug=slug).exists()

        if not exists:
            break

        # Generate new slug
        if counter == 1:
            if len(original_slug) > (max_length - 7):  # Leave room for _XXXXX
                base = original_slug[: (max_length - 7)]
            else:
                base = original_slug
            slug = f"{base}_{generate_charset(5)}"
        else:
            if len(original_slug) > (max_length - len(str(counter)) - 1):
                base = original_slug[: (max_length - len(str(counter)) - 1)]
            else:
                base = original_slug
            slug = f"{base}_{counter}"

        counter += 1

    return slug


def save_image_as_png(image_data: bytes, mime_type: str) -> str | None:
    """Convert image data to PNG and save temporarily."""
    try:
        if not image_data:
            return None

        img = Image.open(BytesIO(image_data))
        temp_path = f"/tmp/{generate_charset(10)}.png"
        img.save(temp_path, "PNG")
        return temp_path
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None


def get_or_create_album(album_name: str, authors: list[Author]) -> Album | None:
    """Get or create album with proper locking and uniqueness check."""
    if not album_name:
        return None

    with transaction.atomic():
        # Try to find existing album
        album = (
            Album.objects.select_for_update().filter(name__iexact=album_name).first()
        )

        if album:
            # Add any missing authors
            current_author_ids = set(album.authors.values_list("id", flat=True))
            new_author_ids = {author.id for author in authors}
            missing_authors = new_author_ids - current_author_ids
            if missing_authors:
                album.authors.add(*missing_authors)
            return album

        try:
            # Create new album
            album = Album.objects.create(
                name=album_name, slug=generate_unique_slug(album_name, Album)
            )
            album.authors.set(authors)
            return album
        except IntegrityError:
            # Handle race condition
            album = (
                Album.objects.select_for_update()
                .filter(name__iexact=album_name)
                .first()
            )
            if album:
                album.authors.add(*authors)
                return album
            raise


def check_song_exists(title: str, album: Album | None, authors: list[Author]) -> bool:
    """Check if a song already exists with the given title, album and authors."""
    query = Song.objects.filter(name__iexact=title)

    if album:
        query = query.filter(album=album)

    if authors:
        # Ensure exact author match
        query = query.annotate(author_count=Count("authors")).filter(
            author_count=len(authors), authors__in=authors
        )

    return query.exists()


def load_mp3_directory(
    directory_path: str, user_id: int | None = None
) -> tuple[list[str], int]:
    """
    Load all MP3 files from a directory and its subdirectories.
    Returns tuple of (failed_files, processed_count)
    """
    path = Path(directory_path)
    failed_files = []
    processed_count = 0

    for mp3_path in path.glob("**/*.mp3"):
        try:
            metadata = extract_mp3_metadata(str(mp3_path))
            if not metadata:
                failed_files.append(str(mp3_path))
                continue

            with transaction.atomic():
                # Process authors
                author_names = process_authors_string(metadata["artists"])
                authors = []
                for author_name in author_names:
                    author = Author.objects.filter(name__iexact=author_name).first()
                    if not author:
                        author = Author.objects.create(
                            name=author_name,
                            slug=generate_unique_slug(author_name, Author),
                        )
                    authors.append(author)

                # Process album
                album = None
                if metadata["album"]:
                    try:
                        album = get_or_create_album(metadata["album"], authors)
                    except IntegrityError as e:
                        print(f"Error creating album for {mp3_path}: {str(e)}")
                        failed_files.append(str(mp3_path))
                        continue

                # Check for existing song
                if check_song_exists(metadata["title"], album, authors):
                    print(f"Skipping existing song: {metadata['title']}")
                    continue

                # Process cover image
                temp_image_path = None
                if metadata["image_data"]:
                    temp_image_path = save_image_as_png(
                        metadata["image_data"], metadata["image_mime"]
                    )
                    if album and not album.image and temp_image_path:
                        with open(temp_image_path, "rb") as img_file:
                            album.image.save(
                                f"{album.slug}.png", File(img_file), save=True
                            )

                # Create song with proper slug from file name
                file_name = os.path.splitext(os.path.basename(str(mp3_path)))[0]
                song = Song(
                    name=metadata["title"],
                    length=metadata["length"],
                    album=album,
                    slug=generate_unique_slug(file_name, Song),
                    creator=User.objects.get(id=user_id) if user_id else None,
                    meta={
                        "genre": metadata["genre"],
                        "release_year": metadata["release_year"],
                    },
                )

                # Save files
                with open(mp3_path, "rb") as mp3_file:
                    song.file.save(f"{song.slug}.mp3", File(mp3_file), save=True)

                if temp_image_path:
                    with open(temp_image_path, "rb") as img_file:
                        song.image.save(f"{song.slug}.png", File(img_file), save=True)
                    os.remove(temp_image_path)

                # Set authors
                song.authors.set(authors)
                processed_count += 1

        except Exception as e:
            print(f"Error processing {mp3_path}: {str(e)}")
            failed_files.append(str(mp3_path))

    return failed_files, processed_count
