from datetime import timedelta

import pylast
import structlog
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import now
from pytube import Channel, Playlist

from akarpov.music.api.serializers import SongSerializer
from akarpov.music.models import (
    AnonMusicUser,
    AnonMusicUserHistory,
    RadioSong,
    Song,
    UserListenHistory,
    UserMusicProfile,
)
from akarpov.music.services import yandex, youtube
from akarpov.music.services.file import load_dir, load_file
from akarpov.utils.celery import get_scheduled_tasks_name

logger = structlog.get_logger(__name__)


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
    yb = yandex.load_file_meta(track, user_id)
    return yb


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


@shared_task
def listen_to_song(song_id, user_id=None, anon=True):
    # protection from multiple listen,
    # check that last listen by user was more than the length of the song
    # and last listened song is not the same
    s = Song.objects.get(id=song_id)
    s.played += 1
    s.save(update_fields=["played"])
    if user_id:
        if anon:
            try:
                anon_user = AnonMusicUser.objects.get(id=user_id)
            except AnonMusicUser.DoesNotExist:
                anon_user = AnonMusicUser.objects.create(id=user_id)
            try:
                last_listen = AnonMusicUserHistory.objects.filter(
                    user_id=user_id
                ).last()
            except AnonMusicUserHistory.DoesNotExist:
                last_listen = None
            if (
                last_listen
                and last_listen.song_id == song_id
                or last_listen
                and last_listen.created + timedelta(seconds=s.length) > now()
            ):
                return
            AnonMusicUserHistory.objects.create(
                user=anon_user,
                song_id=song_id,
            )
        else:
            try:
                last_listen = UserListenHistory.objects.filter(user_id=user_id).last()
            except UserListenHistory.DoesNotExist:
                last_listen = None
            if (
                last_listen
                and last_listen.song_id == song_id
                or last_listen
                and last_listen.created + timedelta(seconds=s.length) > now()
            ):
                return
            UserListenHistory.objects.create(
                user_id=user_id,
                song_id=song_id,
            )
            try:
                user_profile = UserMusicProfile.objects.get(user_id=user_id)
                lastfm_token = user_profile.lastfm_token

                # Initialize Last.fm network with the user's session key
                network = pylast.LastFMNetwork(
                    api_key=settings.LAST_FM_API_KEY,
                    api_secret=settings.LAST_FM_SECRET,
                    session_key=lastfm_token,
                )
                song = Song.objects.get(id=song_id)
                artist_name = song.artists_names
                track_name = song.name
                timestamp = int(timezone.now().timestamp())
                network.scrobble(
                    artist=artist_name, title=track_name, timestamp=timestamp
                )
            except UserMusicProfile.DoesNotExist:
                pass
            except Exception as e:
                logger.error(f"Last.fm scrobble error: {e}")
    return song_id
