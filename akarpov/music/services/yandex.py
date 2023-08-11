import os
from pathlib import Path
from random import randint

from django.conf import settings
from django.core.files import File
from django.utils.text import slugify
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3, TCON, TORY
from mutagen.mp3 import MP3
from pydub import AudioSegment
from yandex_music import Client, Playlist, Search, Track

from akarpov.music import tasks
from akarpov.music.models import Album, Author, Song, SongInQue


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


def load_file_meta(track: int):
    que = SongInQue.objects.create()
    try:
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
        orig_path = f"{settings.MEDIA_ROOT}/{filename}"

        track.download(filename=orig_path, codec="mp3")

        path = orig_path + ".mp3"
        AudioSegment.from_file(orig_path).export(path)
        os.remove(orig_path)

        # load album image
        img_pth = str(settings.MEDIA_ROOT + f"/_{str(randint(10000, 99999))}.png")

        track.download_cover(filename=img_pth)

        album = track.albums[0]

        # set music meta
        tag = MP3(path, ID3=ID3)
        tag.tags.add(
            APIC(
                encoding=3,  # 3 is for utf-8
                mime="image/png",  # image/jpeg or image/png
                type=3,  # 3 is for the cover image
                desc="Cover",
                data=open(img_pth, "rb").read(),
            )
        )
        tag.tags.add(TORY(text=str(album.year)))
        tag.tags.add(TCON(text=album.genre))
        tag.save()

        os.remove(img_pth)
        tag = EasyID3(path)

        tag["title"] = track.title
        tag["album"] = album.title
        tag["artist"] = track.artists[0].name

        tag.save()

        # save track
        ms_path = Path(path)
        song = Song(
            name=track.title,
            author=Author.objects.get_or_create(name=track.artists[0].name)[0],
            album=Album.objects.get_or_create(name=album.title)[0],
        )
        with ms_path.open(mode="rb") as f:
            song.file = File(f, name=ms_path.name)
            song.save()
        os.remove(path)
        que.delete()
        return song
    except Exception as e:
        que.name = e
        que.error = True
        que.save()


def load_playlist(link: str):
    author = link.split("/")[4]
    playlist_id = link.split("/")[-1]

    client = login()
    playlist = client.users_playlists(int(playlist_id), author)  # type: Playlist
    for track in playlist.fetch_tracks():
        tasks.load_ym_file_meta.apply_async(kwargs={"track": track.track.id})
