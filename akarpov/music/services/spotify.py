import spotipy
from django.conf import settings
from spotipy.oauth2 import SpotifyClientCredentials


def login() -> spotipy.Spotify:
    if not settings.MUSIC_SPOTIFY_ID or not settings.MUSIC_SPOTIFY_SECRET:
        raise ConnectionError("No spotify credentials provided")
    return spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=settings.MUSIC_SPOTIFY_ID,
            client_secret=settings.MUSIC_SPOTIFY_SECRET,
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
    try:
        res = search(name)["tracks"]["items"]
    except TypeError:
        return info
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
    if genres:
        info["genre"] = genres[0]

    return info
