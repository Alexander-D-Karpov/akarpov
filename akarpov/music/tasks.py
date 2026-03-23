import os
import tempfile
import time
from datetime import timedelta

import pylast
import requests
import structlog
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils.timezone import now

from akarpov.music.api.serializers import SongSerializer
from akarpov.music.models import Album as AlbumModel
from akarpov.music.models import (
    AnonMusicUser,
    AnonMusicUserHistory,
    Author,
    DownloadJob,
    DownloadTrack,
    Playlist,
    PlaylistSong,
    RadioSong,
    Song,
    UserListenHistory,
    UserMusicProfile,
)
from akarpov.music.services.db import load_track
from akarpov.music.services.download import (
    ConfigProvider,
    SpotifyRateLimitError,
    TrackMeta,
    clear_spotify_rate_limit,
    create_spotify_session,
    detect_source,
    download_audio,
    download_soundcloud_track,
    is_spotify_rate_limited,
    resolve_soundcloud_url,
    resolve_spotify_url,
    resolve_youtube_url,
    safe_spotify_call,
    search_youtube_music,
    send_job_update,
    send_track_update,
)
from akarpov.music.services.file import set_song_volume
from akarpov.utils.celery import get_scheduled_tasks_name

logger = structlog.get_logger(__name__)


def _get_provider(job: DownloadJob) -> ConfigProvider:
    return ConfigProvider(job.config)


def _create_playlist_for_job(job: DownloadJob, playlist_name: str) -> Playlist:
    if not playlist_name:
        playlist_name = f"Download {job.id}"

    playlist = Playlist.objects.create(
        name=playlist_name,
        private=False,
        creator=job.creator,
    )
    job.playlist_name = playlist_name
    job.created_playlist = playlist
    job.save(update_fields=["playlist_name", "created_playlist"])
    return playlist


def _add_song_to_playlist(playlist: Playlist, song: Song):
    if not playlist or not song:
        return
    if PlaylistSong.objects.filter(playlist=playlist, song=song).exists():
        return
    order = PlaylistSong.objects.filter(playlist=playlist).count()
    PlaylistSong.objects.create(playlist=playlist, song=song, order=order)


def _find_existing_song(name: str, artists: list) -> Song | None:
    if not name:
        return None
    qs = Song.objects.filter(name__iexact=name)
    if artists:
        for artist_name in artists[:2]:
            qs = qs.filter(authors__name__iexact=artist_name)
    song = qs.first()
    return song


@shared_task(bind=True, soft_time_limit=3600 * 4, time_limit=3600 * 5)
def process_download_job(self, job_id: int):
    try:
        job = DownloadJob.objects.get(id=job_id)
    except DownloadJob.DoesNotExist:
        return

    job.celery_task_id = self.request.id or ""
    job.status = DownloadJob.Status.RESOLVING
    job.save(update_fields=["celery_task_id", "status"])
    send_job_update(job)

    source = detect_source(job.url)
    job.source = source
    job.save(update_fields=["source"])

    try:
        if source == DownloadJob.Source.SPOTIFY:
            _process_spotify_job(job)
        elif source == DownloadJob.Source.YOUTUBE:
            _process_youtube_job(job)
        elif source == DownloadJob.Source.YANDEX:
            _process_yandex_job(job)
        elif source == DownloadJob.Source.SOUNDCLOUD:
            _process_soundcloud_job(job)
        else:
            _process_fallback_job(job)
    except SpotifyRateLimitError:
        _mark_job_rate_limited(job)
        retry_spotify_jobs.apply_async(countdown=25 * 3600)
        return
    except Exception as e:
        job.status = DownloadJob.Status.FAILED
        job.error = str(e)[:500]
        job.save(update_fields=["status", "error"])
        send_job_update(job)
        logger.error("Download job failed", job_id=job.id, error=str(e))
        return

    failed = job.tracks.filter(status=DownloadTrack.Status.FAILED).count()
    completed = job.tracks.filter(status=DownloadTrack.Status.COMPLETED).count()
    skipped = job.tracks.filter(status=DownloadTrack.Status.SKIPPED).count()

    if failed == job.total_tracks and job.total_tracks > 0:
        job.status = DownloadJob.Status.FAILED
    else:
        job.status = DownloadJob.Status.COMPLETED
    job.processed_tracks = completed + skipped
    job.save(update_fields=["status", "processed_tracks"])
    send_job_update(job)


def _process_spotify_job(job: DownloadJob):
    if is_spotify_rate_limited():
        raise SpotifyRateLimitError("Spotify is rate limited")

    provider = _get_provider(job)
    try:
        resolve_result = resolve_spotify_url(job.url, provider)
    except SpotifyRateLimitError:
        raise

    playlist = None
    if resolve_result.is_playlist and resolve_result.playlist_name:
        playlist = _create_playlist_for_job(job, resolve_result.playlist_name)

    job.total_tracks = len(resolve_result.tracks)
    job.status = DownloadJob.Status.PROCESSING
    job.save(update_fields=["total_tracks", "status"])
    send_job_update(job)

    for meta in resolve_result.tracks:
        existing = _find_existing_song(meta.name, meta.artists)
        if existing:
            dt = DownloadTrack.objects.create(
                job=job,
                name=meta.name,
                artist_name=", ".join(meta.artists),
                album_name=meta.album,
                spotify_url=meta.spotify_url,
                duration_ms=meta.duration_ms,
                status=DownloadTrack.Status.SKIPPED,
                song=existing,
            )
            _add_song_to_playlist(playlist, existing)
            send_track_update(dt)
            _bump_job_progress(job)
            continue

        dt = DownloadTrack.objects.create(
            job=job,
            name=meta.name,
            artist_name=", ".join(meta.artists),
            album_name=meta.album,
            spotify_url=meta.spotify_url,
            duration_ms=meta.duration_ms,
            status=DownloadTrack.Status.PENDING,
        )
        song = _download_single_track(dt, meta, provider)
        if song:
            _add_song_to_playlist(playlist, song)


def _process_youtube_job(job: DownloadJob):
    provider = _get_provider(job)
    resolve_result = resolve_youtube_url(job.url)

    playlist = None
    if resolve_result.is_playlist and resolve_result.playlist_name:
        playlist = _create_playlist_for_job(job, resolve_result.playlist_name)

    job.total_tracks = len(resolve_result.tracks)
    job.status = DownloadJob.Status.PROCESSING
    job.save(update_fields=["total_tracks", "status"])
    send_job_update(job)

    for yt in resolve_result.tracks:
        name = yt.get("name", "")
        artists = yt.get("artists", [])
        existing = _find_existing_song(name, artists)
        if existing:
            dt = DownloadTrack.objects.create(
                job=job,
                name=name,
                artist_name=", ".join(artists),
                youtube_url=yt["url"],
                duration_ms=yt.get("duration_ms", 0),
                status=DownloadTrack.Status.SKIPPED,
                song=existing,
            )
            _add_song_to_playlist(playlist, existing)
            send_track_update(dt)
            _bump_job_progress(job)
            continue

        dt = DownloadTrack.objects.create(
            job=job,
            name=name,
            artist_name=", ".join(artists),
            youtube_url=yt["url"],
            duration_ms=yt.get("duration_ms", 0),
            status=DownloadTrack.Status.PENDING,
        )
        song = _download_single_yt_track(dt, yt, provider)
        if song:
            _add_song_to_playlist(playlist, song)


def _process_soundcloud_job(job: DownloadJob):
    provider = _get_provider(job)
    resolve_result = resolve_soundcloud_url(job.url, provider)

    sc_client_id = getattr(resolve_result, "_sc_client_id", None)
    if not sc_client_id:
        from akarpov.music.services.download import _get_soundcloud_client_id

        sc_client_id = _get_soundcloud_client_id(provider)
    if not sc_client_id:
        job.status = DownloadJob.Status.FAILED
        job.error = "Could not obtain SoundCloud client_id"
        job.save(update_fields=["status", "error"])
        send_job_update(job)
        return

    playlist = None
    if resolve_result.is_playlist and resolve_result.playlist_name:
        playlist = _create_playlist_for_job(job, resolve_result.playlist_name)

    job.total_tracks = len(resolve_result.tracks)
    job.status = DownloadJob.Status.PROCESSING
    job.save(update_fields=["total_tracks", "status"])
    send_job_update(job)

    for sc_track in resolve_result.tracks:
        name = sc_track.get("name", "")
        artists = sc_track.get("artists", [])
        existing = _find_existing_song(name, artists)
        if existing:
            dt = DownloadTrack.objects.create(
                job=job,
                name=name,
                artist_name=", ".join(artists),
                status=DownloadTrack.Status.SKIPPED,
                song=existing,
            )
            _add_song_to_playlist(playlist, existing)
            send_track_update(dt)
            _bump_job_progress(job)
            continue

        dt = DownloadTrack.objects.create(
            job=job,
            name=name,
            artist_name=", ".join(artists),
            duration_ms=sc_track.get("duration_ms", 0),
            status=DownloadTrack.Status.PENDING,
        )
        song = _download_single_sc_track(dt, sc_track, sc_client_id, provider)
        if song:
            _add_song_to_playlist(playlist, song)


def _process_yandex_job(job: DownloadJob):
    from akarpov.music.services import yandex

    job.status = DownloadJob.Status.PROCESSING
    job.total_tracks = 1
    job.save(update_fields=["status", "total_tracks"])
    send_job_update(job)
    try:
        yandex.load_url(job.url, job.creator_id)
        job.processed_tracks = 1
        job.status = DownloadJob.Status.COMPLETED
    except Exception as e:
        job.status = DownloadJob.Status.FAILED
        job.error = str(e)[:500]
    job.save(update_fields=["status", "processed_tracks", "error"])
    send_job_update(job)


def _process_fallback_job(job: DownloadJob):
    provider = _get_provider(job)
    try:
        sp = create_spotify_session(provider)
        results = safe_spotify_call(sp.search, q=job.url, type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])
        if items:
            spotify_url = items[0]["external_urls"]["spotify"]
            job.url = spotify_url
            job.source = DownloadJob.Source.SPOTIFY
            job.save(update_fields=["url", "source"])
            _process_spotify_job(job)
            return
    except SpotifyRateLimitError:
        raise
    except Exception:
        pass

    job.status = DownloadJob.Status.FAILED
    job.error = "Could not find handler for URL"
    job.save(update_fields=["status", "error"])
    send_job_update(job)


def _bump_job_progress(job: DownloadJob):
    job.processed_tracks = job.tracks.filter(
        status__in=[
            DownloadTrack.Status.COMPLETED,
            DownloadTrack.Status.SKIPPED,
            DownloadTrack.Status.FAILED,
        ]
    ).count()
    job.save(update_fields=["processed_tracks"])
    send_job_update(job)


def _download_single_track(
    dt: DownloadTrack, meta: TrackMeta, provider: ConfigProvider
) -> Song | None:
    dt.status = DownloadTrack.Status.SEARCHING
    dt.save(update_fields=["status"])
    send_track_update(dt)

    artist_str = ", ".join(meta.artists) if meta.artists else ""

    try:
        yt_url = search_youtube_music(meta.name, artist_str, meta.duration_ms)
    except Exception as e:
        dt.status = DownloadTrack.Status.FAILED
        dt.error = f"YT Music search failed: {e}"
        dt.save(update_fields=["status", "error"])
        send_track_update(dt)
        _bump_job_progress(dt.job)
        return None

    if not yt_url:
        dt.status = DownloadTrack.Status.FAILED
        dt.error = "No YouTube Music match found"
        dt.save(update_fields=["status", "error"])
        send_track_update(dt)
        _bump_job_progress(dt.job)
        return None

    dt.youtube_url = yt_url
    dt.status = DownloadTrack.Status.DOWNLOADING
    dt.save(update_fields=["youtube_url", "status"])
    send_track_update(dt)

    output_path = os.path.join(settings.MEDIA_ROOT, f"dl_{dt.id}_%(title)s.%(ext)s")
    mp3_path = download_audio(yt_url, output_path, provider)

    if not mp3_path or not os.path.exists(mp3_path):
        dt.status = DownloadTrack.Status.FAILED
        dt.error = "yt-dlp download failed"
        dt.save(update_fields=["status", "error"])
        send_track_update(dt)
        _bump_job_progress(dt.job)
        return None

    dt.status = DownloadTrack.Status.PROCESSING
    dt.save(update_fields=["status"])
    send_track_update(dt)

    return _process_downloaded_file(dt, mp3_path, meta, provider)


def _download_single_yt_track(
    dt: DownloadTrack, yt_info: dict, provider: ConfigProvider
) -> Song | None:
    dt.status = DownloadTrack.Status.DOWNLOADING
    dt.save(update_fields=["status"])
    send_track_update(dt)

    output_path = os.path.join(settings.MEDIA_ROOT, f"dl_{dt.id}_%(title)s.%(ext)s")
    mp3_path = download_audio(yt_info["url"], output_path, provider)

    if not mp3_path or not os.path.exists(mp3_path):
        dt.status = DownloadTrack.Status.FAILED
        dt.error = "yt-dlp download failed"
        dt.save(update_fields=["status", "error"])
        send_track_update(dt)
        _bump_job_progress(dt.job)
        return None

    dt.status = DownloadTrack.Status.PROCESSING
    dt.save(update_fields=["status"])
    send_track_update(dt)

    title = yt_info.get("name", "") or os.path.splitext(os.path.basename(mp3_path))[0]
    meta = TrackMeta(
        name=title,
        artists=yt_info.get("artists", []),
        spotify_url=yt_info.get("url", ""),
    )
    return _process_downloaded_file(dt, mp3_path, meta, provider)


def _download_single_sc_track(
    dt: DownloadTrack, sc_track: dict, sc_client_id: str, provider: ConfigProvider
) -> Song | None:
    dt.status = DownloadTrack.Status.DOWNLOADING
    dt.save(update_fields=["status"])
    send_track_update(dt)

    permalink_url = sc_track.get("permalink_url", "")
    if not permalink_url:
        dt.status = DownloadTrack.Status.FAILED
        dt.error = "No permalink URL"
        dt.save(update_fields=["status", "error"])
        send_track_update(dt)
        _bump_job_progress(dt.job)
        return None

    tmpdir = tempfile.mkdtemp(prefix="sc_dl_")
    try:
        mp3_path = download_soundcloud_track(permalink_url, tmpdir, sc_client_id)
        if not mp3_path or not os.path.exists(mp3_path):
            dt.status = DownloadTrack.Status.FAILED
            dt.error = "scdl download failed"
            dt.save(update_fields=["status", "error"])
            send_track_update(dt)
            _bump_job_progress(dt.job)
            return None

        dt.status = DownloadTrack.Status.PROCESSING
        dt.save(update_fields=["status"])
        send_track_update(dt)

        image_path = None
        artwork_url = sc_track.get("artwork_url", "")
        if artwork_url:
            try:
                r = requests.get(artwork_url, timeout=15)
                if r.status_code == 200:
                    image_path = os.path.join(tmpdir, "cover.png")
                    with open(image_path, "wb") as f:
                        f.write(r.content)
            except Exception:
                pass

        meta = TrackMeta(
            name=sc_track.get("name", ""),
            artists=sc_track.get("artists", []),
            album_image_url=artwork_url,
        )

        return _process_downloaded_file(
            dt, mp3_path, meta, provider, image_path=image_path
        )
    finally:
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)


def _process_downloaded_file(
    dt: DownloadTrack,
    mp3_path: str,
    meta: TrackMeta,
    provider: ConfigProvider,
    image_path: str = None,
) -> Song | None:
    from random import randint

    import requests as req

    from akarpov.music.services.info import search_all_platforms

    try:
        query = f"{', '.join(meta.artists)} {meta.name}".strip()
        info = search_all_platforms(query) if query else {}

        if not image_path and not info.get("album_image") and meta.album_image_url:
            try:
                r = req.get(meta.album_image_url, timeout=15)
                if r.status_code == 200:
                    image_path = os.path.join(
                        settings.MEDIA_ROOT, f"tmp_{randint(10000, 99999)}.png"
                    )
                    with open(image_path, "wb") as f:
                        f.write(r.content)
            except Exception:
                pass

        song = load_track(
            path=mp3_path,
            image_path=image_path or info.get("album_image"),
            user_id=dt.job.creator_id,
            authors=meta.artists or info.get("artists", []),
            album=meta.album or info.get("album_name", ""),
            name=meta.name or info.get("title", ""),
            link=meta.spotify_url,
            genre=meta.genre or info.get("genre"),
            release=meta.release or info.get("release"),
            explicit=meta.explicit,
        )

        if song and hasattr(song, "id") and song.id:
            dt.song = song
            dt.name = song.name
            dt.artist_name = song.artists_names or dt.artist_name
            dt.status = DownloadTrack.Status.COMPLETED
            dt.save(update_fields=["song", "name", "artist_name", "status"])
            try:
                set_song_volume(song)
            except Exception:
                pass
            send_track_update(dt)
            _bump_job_progress(dt.job)
            time.sleep(1)
            return song
        else:
            dt.status = DownloadTrack.Status.FAILED
            dt.error = "load_track returned no song"
            dt.save(update_fields=["status", "error"])
    except Exception as e:
        dt.status = DownloadTrack.Status.FAILED
        dt.error = str(e)[:500]
        dt.save(update_fields=["status", "error"])

    send_track_update(dt)
    _bump_job_progress(dt.job)
    time.sleep(1)
    return None


@shared_task
def retry_spotify_jobs():
    if is_spotify_rate_limited():
        retry_spotify_jobs.apply_async(countdown=3600)
        return

    clear_spotify_rate_limit()
    jobs = DownloadJob.objects.filter(
        source=DownloadJob.Source.SPOTIFY,
        status=DownloadJob.Status.RATE_LIMITED,
    )
    for job in jobs:
        job.status = DownloadJob.Status.PENDING
        job.error = ""
        job.save(update_fields=["status", "error"])
        job.tracks.filter(status=DownloadTrack.Status.RATE_LIMITED).update(
            status=DownloadTrack.Status.PENDING, error=""
        )
        process_download_job.apply_async(kwargs={"job_id": job.id})


def _mark_job_rate_limited(job: DownloadJob):
    job.status = DownloadJob.Status.RATE_LIMITED
    job.error = "Spotify rate limited — will retry in 25h"
    job.save(update_fields=["status", "error"])
    send_job_update(job)

    job.tracks.filter(
        status__in=[DownloadTrack.Status.PENDING, DownloadTrack.Status.SEARCHING]
    ).update(status=DownloadTrack.Status.RATE_LIMITED, error="Spotify rate limited")

    DownloadJob.objects.filter(
        source=DownloadJob.Source.SPOTIFY,
        status__in=[
            DownloadJob.Status.PENDING,
            DownloadJob.Status.RESOLVING,
            DownloadJob.Status.PROCESSING,
        ],
    ).exclude(id=job.id).update(
        status=DownloadJob.Status.RATE_LIMITED,
        error="Spotify rate limited — will retry in 25h",
    )


@shared_task
def process_file_upload(path, user_id):
    from akarpov.music.services.file import load_file

    load_file(path, user_id)
    return path


@shared_task
def process_dir_upload(path, user_id):
    from akarpov.music.services.file import load_dir

    load_dir(path, user_id)
    return path


@shared_task()
def start_next_song(previous_ids: list):
    f = Song.objects.filter(length__isnull=False).exclude(id__in=previous_ids)
    if not f:
        previous_ids = []
        f = Song.objects.filter(length__isnull=False)
    if not f:
        if "akarpov.music.tasks.start_next_song" not in get_scheduled_tasks_name():
            start_next_song.apply_async(kwargs={"previous_ids": []}, countdown=60)
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
                kwargs={"previous_ids": previous_ids}, countdown=song.length
            )


@shared_task
def listen_to_song(song_id, user_id=None, anon=True):
    from django.utils import timezone

    s = Song.objects.get(id=song_id)
    s.played += 1
    s.save(update_fields=["played"])

    if not user_id:
        return song_id

    if anon:
        try:
            anon_user = AnonMusicUser.objects.get(id=user_id)
        except AnonMusicUser.DoesNotExist:
            anon_user = AnonMusicUser.objects.create(id=user_id)
        try:
            last_listen = AnonMusicUserHistory.objects.filter(user_id=user_id).last()
        except AnonMusicUserHistory.DoesNotExist:
            last_listen = None
        if (
            last_listen
            and last_listen.song_id == song_id
            or last_listen
            and last_listen.created + timedelta(seconds=s.length or 300) > now()
        ):
            return
        AnonMusicUserHistory.objects.create(user=anon_user, song_id=song_id)
    else:
        try:
            last_listen = UserListenHistory.objects.filter(user_id=user_id).last()
        except UserListenHistory.DoesNotExist:
            last_listen = None
        if (
            last_listen
            and last_listen.song_id == song_id
            or last_listen
            and last_listen.created + timedelta(seconds=s.length or 300) > now()
        ):
            return
        UserListenHistory.objects.create(user_id=user_id, song_id=song_id)
        try:
            user_profile = UserMusicProfile.objects.get(user_id=user_id)
            lastfm_token = user_profile.lastfm_token
            network = pylast.LastFMNetwork(
                api_key=settings.LAST_FM_API_KEY,
                api_secret=settings.LAST_FM_SECRET,
                session_key=lastfm_token,
            )
            song = Song.objects.get(id=song_id)
            timestamp = int(timezone.now().timestamp())
            network.scrobble(
                artist=song.get_first_author_name(),
                title=song.name,
                timestamp=timestamp,
                album=song.album.name if song.album else "",
            )
            network.update_now_playing(
                artist=song.get_first_author_name(),
                title=song.name,
                album=song.album.name if song.album else "",
            )
        except UserMusicProfile.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Last.fm scrobble error: {e}")

    return song_id


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def update_author_info_task(self, author_id: int):
    try:
        author = Author.objects.get(id=author_id)
    except Author.DoesNotExist:
        return
    from akarpov.music.services.info import update_author_info

    try:
        update_author_info(author)
    except Exception as e:
        logger.warning(
            "update_author_info_task failed", author_id=author_id, error=str(e)
        )
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def update_album_info_task(self, album_id: int):
    try:
        album = AlbumModel.objects.get(id=album_id)
    except AlbumModel.DoesNotExist:
        return
    from akarpov.music.services.info import update_album_info

    authors = album.authors.all()
    author_name = authors.first().name if authors.exists() else None
    try:
        update_album_info(album, author_name)
    except Exception as e:
        logger.warning("update_album_info_task failed", album_id=album_id, error=str(e))
        raise self.retry(exc=e)


@shared_task
def load_ym_file_meta(track: int, user_id: int):
    from akarpov.music.services.yandex import load_file_meta

    return load_file_meta(track, user_id)
