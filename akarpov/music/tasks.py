from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from pytube import Channel, Playlist

from akarpov.music.api.serializers import SongSerializer
from akarpov.music.models import RadioSong, Song
from akarpov.music.services import yandex, youtube
from akarpov.music.services.file import load_dir, load_file
from akarpov.utils.celery import get_scheduled_tasks_name


@shared_task
def list_tracks(url, user_id):
    if "music.yandex.ru" in url:
        yandex.load_playlist(url, user_id)
    elif "channel" in url or "/c/" in url:
        p = Channel(url)
        for video in p.video_urls:
            process_yb.apply_async(kwargs={"url": video, "user_id": user_id})
    elif "playlist" in url or "&list=" in url:
        p = Playlist(url)
        for video in p.video_urls:
            process_yb.apply_async(kwargs={"url": video, "user_id": user_id})
    else:
        process_yb.apply_async(kwargs={"url": url, "user_id": user_id})

    return url


@shared_task(max_retries=5)
def process_yb(url, user_id):
    youtube.download_from_youtube_link(url, user_id)
    return url


@shared_task
def process_dir(path, user_id):
    load_dir(path, user_id)
    return path


@shared_task
def process_file(path, user_id):
    load_file(path, user_id)
    return path


@shared_task
def load_ym_file_meta(track, user_id):
    return yandex.load_file_meta(track, user_id)


@shared_task()
def start_next_song(previous_ids: list):
    f = Song.objects.filter(length__isnull=False).exclude(id__in=previous_ids)
    if not f:
        previous_ids = []
        f = Song.objects.filter(length__isnull=False)
    if not f:
        if "akarpov.music.tasks.start_next_song" not in get_scheduled_tasks_name():
            start_next_song.apply_async(
                kwargs={"previous_ids": []},
                countdown=60,
            )
    else:
        song = f.order_by("?").first()
        data = SongSerializer(context={"request": None}).to_representation(song)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "radio_main", {"type": "song", "data": data}
        )
        song.played += 1
        song.save(update_fields=["played"])
        if RadioSong.objects.filter(slug="").exists():
            r = RadioSong.objects.get(slug="")
            r.song = song
            r.save()
        else:
            RadioSong.objects.create(song=song, slug="")
        previous_ids.append(song.id)
        if "akarpov.music.tasks.start_next_song" not in get_scheduled_tasks_name():
            start_next_song.apply_async(
                kwargs={"previous_ids": previous_ids},
                countdown=song.length,
            )
    return
