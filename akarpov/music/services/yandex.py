import os
from random import randint

from django.conf import settings
from django.core.files import File
from yandex_music import Client, Playlist, Search, Track
from yandex_music.exceptions import NotFoundError

from akarpov.music import tasks
from akarpov.music.models import Album as AlbumModel
from akarpov.music.models import Author, Song, SongInQue
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


def load_playlist(link: str, user_id: int):
    author = link.split("/")[4]
    playlist_id = link.split("/")[-1]

    client = login()
    playlist = client.users_playlists(int(playlist_id), author)  # type: Playlist
    for track in playlist.fetch_tracks():
        tasks.load_ym_file_meta.apply_async(
            kwargs={"track": track.track.id, "user_id": user_id}
        )


def update_album_info(album: AlbumModel) -> None:
    client = login()
    search = client.search(album.name, type_="album")  # type: Search

    if search.albums:
        search_album = search.albums.results[0]
        data = {
            "name": search_album.title,
            "tracks": search_album.track_count,
            "explicit": search_album.explicit,
            "year": search_album.year,
            "genre": search_album.genre,
            "description": search_album.description,
            "type": search_album.type,
        }
        authors = []
        if search_album.artists:
            for x in search_album.artists:
                try:
                    authors.append(Author.objects.get(name=x.name))
                except Author.DoesNotExist:
                    authors.append(Author.objects.create(name=x.name))
        album.authors.set(authors)
        album.meta = data
        image_path = str(settings.MEDIA_ROOT + f"/_{str(randint(10000, 99999))}.png")
        if not search_album.cover_uri:
            album.save()
            return
        search_album.download_cover(filename=image_path)
        with open(image_path, "rb") as f:
            album.image = File(f, name=image_path.split("/")[-1])
            album.save()
        os.remove(image_path)


def update_author_info(author: Author) -> None:
    client = login()
    search = client.search(author.name, type_="artist")  # type: Search

    if search.artists:
        search_artist = search.artists.results[0]
        data = {
            "name": search_artist.name,
            "description": search_artist.description,
            "genres": search_artist.genres,
        }

        author.meta = data

        image_path = str(settings.MEDIA_ROOT + f"/_{str(randint(10000, 99999))}.png")
        if not search_artist.cover:
            author.save()
            return
        search_artist.cover.download(filename=image_path)
        with open(image_path, "rb") as f:
            author.image = File(f, name=image_path.split("/")[-1])
            author.save()
        os.remove(image_path)
