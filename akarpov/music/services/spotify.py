import spotipy
from django.conf import settings
from spotipy.oauth2 import SpotifyClientCredentials

from akarpov.music.services.yandex import search_ym


def login() -> spotipy.Spotify:
    if not settings.SPOTIFY_ID or not settings.SPOTIFY_SECRET:
        raise ConnectionError("No spotify credentials provided")
    return spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=settings.SPOTIFY_ID, client_secret=settings.SPOTIFY_SECRET
        )
    )


def search(name: str, search_type="track"):
    sp = login()
    res = sp.search(name, type=search_type)
    return res


def get_track_info(name: str) -> dict:
    info = {
        "album_name": "",
        "album_image": "",
        "release": "",
        "artists": [],
        "artist": "",
        "title": "",
    }

    res = search(name)["tracks"]["items"]
    if not res:
        return info
    res = res[0]

    info["album_name"] = res["album"]["name"]
    info["release"] = res["album"]["release_date"].split("-")[0]
    info["album_image"] = res["album"]["images"][0]["url"]
    info["artists"] = [x["name"] for x in res["artists"]]
    info["artist"] = [x["name"] for x in res["artists"]][0]
    info["title"] = res["name"]

    # try to get genre
    sp = login()
    genres = sp.album(res["album"]["external_urls"]["spotify"])["genres"]
    if not genres:
        ym_info = search_ym(info["artist"] + " " + info["title"])
        if ym_info and "genre" in ym_info:
            info["genre"] = ym_info["genre"]
        else:
            genres = sp.artist(res["artists"][0]["external_urls"]["spotify"])["genres"]
            if genres:
                info["genre"] = genres[0]
    else:
        info["genre"] = genres[0]

    return info
