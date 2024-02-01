import spotipy
from django.conf import settings
from spotdl import Song, Spotdl
from spotipy.oauth2 import SpotifyClientCredentials

from akarpov.music.services.db import load_track


def create_session() -> spotipy.Spotify:
    if not settings.MUSIC_SPOTIFY_ID or not settings.MUSIC_SPOTIFY_SECRET:
        raise ConnectionError("No spotify credentials provided")

    return spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=settings.MUSIC_SPOTIFY_ID,
            client_secret=settings.MUSIC_SPOTIFY_SECRET,
        )
    )


def search(name: str, session: spotipy.Spotify, search_type="track"):
    res = session.search(name, type=search_type)
    return res


def download_url(url, user_id=None):
    spot_settings = {
        "simple_tui": True,
        "log_level": "ERROR",
        "lyrics_providers": ["genius", "musixmatch"],
    }

    spotdl_client = Spotdl(
        client_id=settings.MUSIC_SPOTIFY_ID,
        client_secret=settings.MUSIC_SPOTIFY_SECRET,
        user_auth=False,
        headless=False,
        downloader_settings=spot_settings,
    )

    session = create_session()

    if "track" in url:
        songs = [Song.from_url(url)]
    elif "album" in url:
        album_tracks = session.album(url)["tracks"]["items"]
        songs = [
            Song.from_url(track["external_urls"]["spotify"]) for track in album_tracks
        ]
    elif "artist" in url:
        artist_top_tracks = session.artist_top_tracks(url)["tracks"]
        songs = [
            Song.from_url(track["external_urls"]["spotify"])
            for track in artist_top_tracks
        ]
    elif "playlist" in url:
        playlist_tracks = session.playlist_items(url)["items"]
        songs = [
            Song.from_url(track["track"]["external_urls"]["spotify"])
            for track in playlist_tracks
        ]
    else:
        return None

    for song in songs:
        res = spotdl_client.download(song)
        if res:
            song, path = res
        else:
            return None
        load_track(
            path=str(path),
            image_path=song.cover_url,
            user_id=user_id,
            authors=song.artists,
            album=song.album_name,
            name=song.name,
            link=song.url,
            genre=song.genres[0] if song.genres else None,
            release=song.date,
        )
