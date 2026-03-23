import os
from random import randint
from time import sleep

import structlog
from django.conf import settings
from yandex_music import Client
from yandex_music.exceptions import NetworkError, NotFoundError

from akarpov.music.services.db import load_track

logger = structlog.get_logger(__name__)


def login() -> Client:
    if not settings.MUSIC_YANDEX_TOKEN:
        raise ConnectionError("No yandex credentials provided")
    return Client(settings.MUSIC_YANDEX_TOKEN).init()


def load_file_meta(track: int, user_id: int) -> str:
    client = login()
    track = client.tracks(track)[0]

    from akarpov.music.models import Song

    try:
        if sng := Song.objects.filter(
            name=track.title, album__name=track.albums[0].title
        ):
            return str(sng.first())
    except (IndexError, Exception):
        pass

    filename = f"_{str(randint(10000, 9999999))}"
    orig_path = f"{settings.MEDIA_ROOT}/{filename}.mp3"
    album = track.albums[0] if track.albums else None
    try:
        track.download(filename=orig_path, codec="mp3")
    except NetworkError:
        sleep(5)
        track.download(filename=orig_path, codec="mp3")

    img_pth = str(settings.MEDIA_ROOT + f"/_{str(randint(10000, 99999))}.png")

    try:
        track.download_cover(filename=img_pth)
    except NotFoundError:
        img_pth = None

    try:
        lyrics = track.get_lyrics("LRC").fetch_lyrics()
    except (NotFoundError, Exception):
        lyrics = ""

    song = load_track(
        orig_path,
        img_pth,
        user_id,
        [x.name for x in track.artists],
        album.title if album else "",
        track.title,
        release=album.release_date if album else None,
        genre=album.genre if album else None,
        lyrics=lyrics,
        explicit=track.explicit,
        track_source=getattr(track, "track_source", None),
    )

    try:
        if os.path.exists(orig_path):
            os.remove(orig_path)
        if img_pth and os.path.exists(img_pth):
            os.remove(img_pth)
    except OSError:
        pass

    return str(song) if song else ""


def load_url(link: str, user_id: int):
    client = login()
    obj_id = link.split("/")[-1]
    obj_id = obj_id.split("?")[0]

    try:
        obj_id = int(obj_id)
    except ValueError:
        logger.error("Invalid yandex link", link=link)
        return None

    if "/playlists/" in link:
        author = link.split("/")[4]
        playlist = client.users_playlists(obj_id, author)

        if hasattr(playlist, "tracks") and playlist.tracks:
            for track_short in playlist.tracks:
                try:
                    if hasattr(track_short, "track") and track_short.track:
                        track_id = track_short.track.id
                    elif hasattr(track_short, "id"):
                        track_id = track_short.id
                    else:
                        continue
                    from akarpov.music import tasks

                    tasks.load_ym_file_meta.apply_async(
                        kwargs={"track": track_id, "user_id": user_id}
                    )
                except Exception as e:
                    logger.warning("Error processing track in playlist", error=str(e))

    elif "/album/" in link:
        album = client.albums_with_tracks(obj_id)
        tracks = []
        if hasattr(album, "volumes") and album.volumes:
            for volume in album.volumes:
                tracks.extend(volume)
        elif hasattr(album, "tracks") and album.tracks:
            tracks = album.tracks

        for track in tracks:
            try:
                track_id = track.id if hasattr(track, "id") else track.track.id
                from akarpov.music import tasks

                tasks.load_ym_file_meta.apply_async(
                    kwargs={"track": track_id, "user_id": user_id}
                )
            except Exception as e:
                logger.warning("Error processing track in album", error=str(e))

    elif "/artist/" in link:
        artist = client.artists(obj_id)[0]
        albums = artist.get_albums(page_size=100)

        for album_short in albums:
            try:
                full_album = client.albums_with_tracks(album_short.id)
                tracks = []
                if hasattr(full_album, "volumes") and full_album.volumes:
                    for volume in full_album.volumes:
                        tracks.extend(volume)
                elif hasattr(full_album, "tracks") and full_album.tracks:
                    tracks = full_album.tracks

                for track in tracks:
                    try:
                        track_id = track.id if hasattr(track, "id") else track.track.id
                        from akarpov.music import tasks

                        tasks.load_ym_file_meta.apply_async(
                            kwargs={"track": track_id, "user_id": user_id}
                        )
                    except Exception as e:
                        logger.warning("Error processing track", error=str(e))
            except Exception as e:
                logger.warning(
                    "Error processing album", error=str(e), album_id=album_short.id
                )
    else:
        from akarpov.music import tasks

        tasks.load_ym_file_meta.apply_async(
            kwargs={"track": obj_id, "user_id": user_id}
        )
