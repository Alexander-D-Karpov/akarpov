import os
from random import randint

import requests
from django.conf import settings
from PIL import Image
from pydub import AudioSegment
from pytube import Search, YouTube

from akarpov.music.models import Song, SongInQue
from akarpov.music.services.db import load_track
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
            + f"/{info['album_image'].split('/')[-1]}_{str(randint(100, 999))}.png"
        )
        with open(img_pth, "wb") as f:
            f.write(r.content)

        im = Image.open(img_pth)
        im.save(str(f"{img_pth}.png"))

        os.remove(img_pth)

        load_track(path, img_pth, info["artists"], info["album_name"])
    except Exception as e:
        print(e)
        que.name = e
        que.error = True
        que.save()


def search_channel(name):
    s = Search(name)
    vid = s.results[0]  # type: YouTube
    return vid.channel_url
