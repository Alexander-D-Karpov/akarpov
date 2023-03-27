import os
from pathlib import Path
from random import randint

import requests
from django.conf import settings
from django.core.files import File
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3, TCON, TORY
from mutagen.mp3 import MP3
from PIL import Image
from pydub import AudioSegment
from pytube import Search, YouTube

from akarpov.music.models import Album, Author, Song, SongInQue
from akarpov.music.services.spotify import get_track_info


def download_from_youtube_link(link: str) -> Song:
    que = SongInQue.objects.create()
    try:
        yt = YouTube(link)

        if yt.length > 900:
            # TODO: add long video splitting
            raise ValueError("Track is too long")

        if not len(yt.streams):
            raise ValueError("There is no such song")

        info = get_track_info(yt.title)
        que.name = info["title"]
        que.save()
        if sng := Song.objects.filter(
            name=info["title"], album__name=info["album_name"]
        ):
            que.delete()
            return sng.first()

        authors = [Author.objects.get_or_create(name=x)[0] for x in info["artists"]]
        album = Album.objects.get_or_create(name=info["album_name"])[0]

        audio = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
        orig_path = audio.download(output_path=settings.MEDIA_ROOT)

        # convert to mp3
        path = orig_path.replace(orig_path.split(".")[-1], "mp3")
        AudioSegment.from_file(orig_path).export(path)
        os.remove(orig_path)

        # load album image
        r = requests.get(info["album_image"])
        img_pth = str(
            settings.MEDIA_ROOT
            + f"/{info['album_image'].split('/')[-1]}_{str(randint(100, 999))}"
        )
        with open(img_pth, "wb") as f:
            f.write(r.content)

        im = Image.open(img_pth)
        im.save(str(f"{img_pth}.png"))

        os.remove(img_pth)

        # set music meta
        tag = MP3(path, ID3=ID3)
        tag.tags.add(
            APIC(
                encoding=3,  # 3 is for utf-8
                mime="image/png",  # image/jpeg or image/png
                type=3,  # 3 is for the cover image
                desc="Cover",
                data=open(str(f"{img_pth}.png"), "rb").read(),
            )
        )
        tag.tags.add(TORY(text=info["release"]))
        if "genre" in info:
            tag.tags.add(TCON(text=info["genre"]))

        tag.save()
        os.remove(str(f"{img_pth}.png"))
        tag = EasyID3(path)

        tag["title"] = info["title"]
        tag["album"] = info["album_name"]
        tag["artist"] = info["artist"]

        tag.save()

        # save track
        ms_path = Path(path)
        song = Song(name=info["title"], author=authors[0], album=album)
        with ms_path.open(mode="rb") as f:
            song.file = File(f, name=ms_path.name)
            song.save()
        os.remove(path)
        que.delete()
        return song
    except Exception as e:
        que.name = e
        que.error = True
        que.save()


def search_channel(name):
    s = Search(name)
    vid = s.results[0]  # type: YouTube
    return vid.channel_url
