import os
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
    frame_length = int(0.5 * sr)
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
