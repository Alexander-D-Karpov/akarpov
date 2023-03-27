from celery import shared_task
from pytube import Channel, Playlist

from akarpov.music.services import yandex, youtube
from akarpov.music.services.file import load_dir


@shared_task
def list_tracks(url):
    if "yandex" in url:
        yandex.load_playlist(url)
    elif "channel" in url or "/c/" in url:
        p = Channel(url)
        for video in p.video_urls:
            process_yb.apply_async(kwargs={"url": video})
    elif "playlist" in url or "&list=" in url:
        p = Playlist(url)
        for video in p.video_urls:
            process_yb.apply_async(kwargs={"url": video})

    else:
        process_yb.apply_async(kwargs={"url": url})

    return url


@shared_task(max_retries=5)
def process_yb(url):
    youtube.download_from_youtube_link(url)
    return url


@shared_task
def process_dir(path):
    load_dir(path)
    return path


@shared_task
def load_ym_file_meta(track):
    return yandex.load_file_meta(track)
