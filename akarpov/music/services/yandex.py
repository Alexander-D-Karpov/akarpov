import os
from random import randint

from django.conf import settings
from django.utils.text import slugify
from yandex_music import Client, Playlist, Search, Track

from akarpov.music import tasks
from akarpov.music.models import Song, SongInQue
from akarpov.music.services.db import load_track


def login() -> Client:
    if not settings.MUSIC_YANDEX_TOKEN:
        raise ConnectionError("No yandex credentials provided")
    return Client(settings.MUSIC_YANDEX_TOKEN).init()


def search_ym(name: str):
    client = login()
    info = {}
    search = client.search(name, type_="track")  # type: Search

    if search.tracks:
        best = search.tracks.results[0]  # type: Track

        info = {
            "artists": [artist.name for artist in best.artists],
            "title": best.title,
        }

        # getting genre
        if best.albums[0].genre:
            genre = best.albums[0].genre
        elif best.artists[0].genres:
            genre = best.artists[0].genres[0]
        else:
            genre = None

        if genre:
            info["genre"] = genre

    return info


def load_file_meta(track: int, user_id: int):
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
            return sng.first()
    except IndexError:
        que.delete()
        return

    filename = slugify(f"{track.artists[0].name} - {track.title}")
    orig_path = f"{settings.MEDIA_ROOT}/{filename}.mp3"
    album = track.albums[0]

    track.download(filename=orig_path, codec="mp3")
    img_pth = str(settings.MEDIA_ROOT + f"/_{str(randint(10000, 99999))}.png")

    track.download_cover(filename=img_pth)
    song = load_track(
        orig_path,
        img_pth,
        user_id,
        [x.name for x in track.artists],
        album.title,
        track.title,
        release=album.release_date,
        genre=album.genre,
    )
    if os.path.exists(orig_path):
        os.remove(orig_path)
    if os.path.exists(img_pth):
        os.remove(img_pth)

    return str(song)


def load_playlist(link: str, user_id: int):
    author = link.split("/")[4]
    playlist_id = link.split("/")[-1]

    client = login()
    playlist = client.users_playlists(int(playlist_id), author)  # type: Playlist
    for track in playlist.fetch_tracks():
        tasks.load_ym_file_meta.apply_async(
            kwargs={"track": track.track.id, "user_id": user_id}
        )
