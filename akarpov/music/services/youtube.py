import datetime
import os
import re
from random import randint

import requests
import yt_dlp
from django.conf import settings
from PIL import Image
from pydub import AudioSegment
from pytube import Search, YouTube
from yt_dlp import YoutubeDL

from akarpov.music.models import Song
from akarpov.music.services.db import load_track
from akarpov.music.services.spotify import get_track_info

final_filename = None


ydl_opts = {
    "format": "m4a/bestaudio/best",
    "postprocessors": [
        {  # Extract audio using ffmpeg
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
        }
    ],
    "outtmpl": f"{settings.MEDIA_ROOT}/%(uploader)s_%(title)s.%(ext)s",
}


def download_file(url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url)
    return info["requested_downloads"][0]["_filename"]


def parse_description(description: str) -> list:
    # Read the description file
    # Split into time and chapter name

    list_of_chapters = []

    # only increment chapter number on a chapter line
    # chapter lines start with timecode
    line_counter = 1
    for line in description.split("\n"):
        result = re.search(r"\(?(\d?[:]?\d+[:]\d+)\)?", line)
        try:
            time_count = datetime.datetime.strptime(result.group(1), "%H:%M:%S")
        except Exception:
            try:
                time_count = datetime.datetime.strptime(result.group(1), "%M:%S")
            except Exception:
                continue
        chap_name = line.replace(result.group(0), "").rstrip(" :\n")
        chap_pos = (
            time_count.timestamp() - datetime.datetime(1900, 1, 1, 0, 0).timestamp()
        ) * 1000
        list_of_chapters.append((str(line_counter).zfill(2), chap_pos, chap_name))
        line_counter += 1

    return list_of_chapters


def download_from_youtube_link(link: str) -> Song:
    song = None

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(link, download=False)
        title = info_dict.get("title", None)
        description = info_dict.get("description", None)
    chapters = parse_description(description)
    orig_path = download_file(link)

    # convert to mp3
    print(f"[processing] {title} converting to mp3")
    path = orig_path.replace(orig_path.split(".")[-1], "mp3")
    AudioSegment.from_file(orig_path).export(path)
    os.remove(orig_path)
    print(f"[processing] {title} converting to mp3: done")

    # split in chapters
    if len(chapters) > 1:
        sound = AudioSegment.from_mp3(path)
        for i in range(len(chapters)):
            if i != len(chapters) - 1:
                print(
                    f"[processing] loading {chapters[i][2]} from {chapters[i][1] // 1000} to",
                    f"{chapters[i + 1][1] // 1000}",
                )
                st = chapters[i][1]
                end = chapters[i + 1][1]
                audio = sound[st:end]
            else:
                print(
                    f"[processing] loading {chapters[i][2]} from {chapters[i][1] // 1000}"
                )
                st = chapters[i][1]
                audio = sound[st:]
            chapter_path = path.split(".")[0] + chapters[i][2] + ".mp3"
            info = get_track_info(chapters[i][2])
            audio.export(chapter_path, format="mp3")
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
            if "genre" in info:
                song = load_track(
                    chapter_path,
                    f"{img_pth}.png",
                    info["artists"],
                    info["album_name"],
                    chapters[i][2],
                    genre=info["genre"],
                )
            else:
                song = load_track(
                    chapter_path,
                    f"{img_pth}.png",
                    info["artists"],
                    info["album_name"],
                    chapters[i][2],
                )
            os.remove(chapter_path)
    else:
        print(f"[processing] loading {title}")

        info = get_track_info(title)
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
        if "genre" in info:
            song = load_track(
                path,
                f"{img_pth}.png",
                info["artists"],
                info["album_name"],
                title,
                genre=info["genre"],
            )
        else:
            song = load_track(
                path,
                f"{img_pth}.png",
                info["artists"],
                info["album_name"],
                title,
            )
    os.remove(path)

    return song


def search_channel(name):
    s = Search(name)
    vid = s.results[0]  # type: YouTube
    return vid.channel_url
