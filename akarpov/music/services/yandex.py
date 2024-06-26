import os
from random import randint
from time import sleep

from django.conf import settings
from yandex_music import Client, Playlist, Track
from yandex_music.exceptions import NetworkError, NotFoundError

from akarpov.music import tasks
from akarpov.music.models import Song, SongInQue
from akarpov.music.services.db import load_track


def login() -> Client:
    if not settings.MUSIC_YANDEX_TOKEN:
        raise ConnectionError("No yandex credentials provided")
    return Client(settings.MUSIC_YANDEX_TOKEN).init()


def load_file_meta(track: int, user_id: int) -> str:
    que = SongInQue.objects.create()
    client = login()
    track = client.tracks(track)[0]  # type: Track
    que.name = track.title
    que.save()

    try:
        if sng := Song.objects.filter(
            name=track.title, album__name=track.albums[0].title
        ):
            que.delete()
            return str(sng.first())
    except IndexError:
        que.delete()
        return ""

    filename = f"_{str(randint(10000, 9999999))}"
    orig_path = f"{settings.MEDIA_ROOT}/{filename}.mp3"
    album = track.albums[0]
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
    except NotFoundError:
        lyrics = ""
    song = load_track(
        orig_path,
        img_pth,
        user_id,
        [x.name for x in track.artists],
        album.title,
        track.title,
        release=album.release_date,
        genre=album.genre,
        lyrics=lyrics,
        explicit=track.explicit,
        track_source=track.track_source,
    )
    if os.path.exists(orig_path):
        os.remove(orig_path)
    if os.path.exists(img_pth):
        os.remove(img_pth)

    return str(song)


def load_url(link: str, user_id: int):
    client = login()
    obj_id = link.split("/")[-1]
    obj_id = obj_id.split("?")[0]
    try:
        obj_id = int(obj_id)
    except ValueError:
        print("Invalid link")
        return None

    if "/playlists/" in link:
        author = link.split("/")[4]

        playlist = client.users_playlists(obj_id, author)  # type: Playlist
        for track in playlist.fetch_tracks():
            tasks.load_ym_file_meta.apply_async(
                kwargs={"track": track.track.id, "user_id": user_id}
            )
    elif "/album/" in link:
        album = client.albums_with_tracks(obj_id)
        for volume in album.volumes:
            for track in volume:
                tasks.load_ym_file_meta.apply_async(
                    kwargs={"track": track.id, "user_id": user_id}
                )
    elif "/artist/" in link:
        artist = client.artists(obj_id)[0]
        albums = artist.get_albums(page_size=100)
        for album in albums:
            for track in album.fetch_tracks():
                tasks.load_ym_file_meta.apply_async(
                    kwargs={"track": track.id, "user_id": user_id}
                )
    else:
        tasks.load_ym_file_meta.apply_async(
            kwargs={"track": obj_id, "user_id": user_id}
        )
