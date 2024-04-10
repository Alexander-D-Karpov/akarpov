from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pylast
import spotipy
import structlog
import ytmusicapi
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import now
from spotipy import SpotifyClientCredentials

from akarpov.music.api.serializers import SongSerializer
from akarpov.music.models import (
    AnonMusicUser,
    AnonMusicUserHistory,
    RadioSong,
    Song,
    UserListenHistory,
    UserMusicProfile,
)
from akarpov.music.services import spotify, yandex, youtube
from akarpov.music.services.file import load_dir, load_file
from akarpov.utils.celery import get_scheduled_tasks_name

logger = structlog.get_logger(__name__)


@shared_task(soft_time_limit=60 * 60, time_limit=60 * 120)
def list_tracks(url, user_id):
    if "music.youtube.com" in url or "youtu.be" in url:
        url = url.replace("music.youtube.com", "youtube.com")
        url = url.replace("youtu.be", "youtube.com")
    if "spotify.com" in url:
        spotify.download_url(url, user_id)
    elif "music.yandex.ru" in url:
        yandex.load_url(url, user_id)
    if "youtube.com" in url:
        if "channel" in url or "/c/" in url:
            ytmusic = ytmusicapi.YTMusic()
            channel_id = url.split("/")[-1]
            channel_songs = ytmusic.get_artist(channel_id)["songs"]["results"]

            for song in channel_songs:
                process_yb.apply_async(
                    kwargs={
                        "url": f"https://youtube.com/watch?v={song['videoId']}",
                        "user_id": user_id,
                    }
                )

        elif "playlist" in url or "&list=" in url:
            ytmusic = ytmusicapi.YTMusic()

            # Parse the URL and the query string
            parsed_url = urlparse(url)
            parsed_qs = parse_qs(parsed_url.query)

            # Get the playlist ID from the parsed query string
            playlist_id = parsed_qs.get("list", [None])[0]

            if playlist_id:
                playlist_songs = ytmusic.get_playlist(playlist_id)["tracks"]

            else:
                raise ValueError("No playlist ID found in the URL.")
            for song in playlist_songs:
                process_yb.apply_async(
                    kwargs={
                        "url": f"https://music.youtube.com/watch?v={song['videoId']}",
                        "user_id": user_id,
                    }
                )
        else:
            process_yb.apply_async(kwargs={"url": url, "user_id": user_id})
    else:
        spotify_manager = SpotifyClientCredentials(
            client_id=settings.MUSIC_SPOTIFY_ID,
            client_secret=settings.MUSIC_SPOTIFY_SECRET,
        )
        spotify_search = spotipy.Spotify(client_credentials_manager=spotify_manager)

        results = spotify_search.search(q=url, type="track", limit=1)
        top_track = (
            results["tracks"]["items"][0] if results["tracks"]["items"] else None
        )

        if top_track:
            spotify.download_url(top_track["external_urls"]["spotify"], user_id)
            url = top_track["external_urls"]["spotify"]

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
                artist_name = song.get_first_author_name()
                track_name = song.name
                album_name = song.album.name
                timestamp = int(timezone.now().timestamp())
                network.scrobble(
                    artist=artist_name,
                    title=track_name,
                    timestamp=timestamp,
                    album=album_name,
                )
                network.update_now_playing(
                    artist=artist_name, title=track_name, album=album_name
                )
            except UserMusicProfile.DoesNotExist:
                pass
            except Exception as e:
                logger.error(f"Last.fm scrobble error: {e}")
    return song_id
