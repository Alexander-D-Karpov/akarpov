import os
import time
from io import BytesIO
from pathlib import Path
from random import randint

import librosa
import mutagen
import numpy as np
from mutagen.id3 import ID3
from PIL import Image, UnidentifiedImageError

from akarpov.music.models import Song
from akarpov.music.services.db import load_track


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
