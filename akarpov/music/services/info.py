import os
from random import randint

import requests
import spotipy
from deep_translator import GoogleTranslator
from django.conf import settings
from django.core.files import File
from django.utils.text import slugify
from spotipy import SpotifyClientCredentials
from yandex_music import Client, Cover

from akarpov.music.models import Album as AlbumModel
from akarpov.music.models import Author
from akarpov.utils.generators import generate_charset
from akarpov.utils.text import is_similar_artist, normalize_text


def create_spotify_session() -> spotipy.Spotify:
    if not settings.MUSIC_SPOTIFY_ID or not settings.MUSIC_SPOTIFY_SECRET:
        raise ConnectionError("No spotify credentials provided")

    return spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=settings.MUSIC_SPOTIFY_ID,
            client_secret=settings.MUSIC_SPOTIFY_SECRET,
        )
    )


def yandex_login() -> Client:
    if not settings.MUSIC_YANDEX_TOKEN:
        raise ConnectionError("No yandex credentials provided")
    return Client(settings.MUSIC_YANDEX_TOKEN).init()


def spotify_search(name: str, session: spotipy.Spotify, search_type="track"):
    res = session.search(name, type=search_type)
    return res


def get_spotify_info(name: str, session: spotipy.Spotify) -> dict:
    info = {
        "album_name": "",
        "album_image": "",
        "release": "",
        "artists": [],
        "artist": "",
        "title": "",
        "genre": "",
    }

    try:
        results = spotify_search(name, session)["tracks"]["items"]
        if not results:
            return info

        track = results[0]
        info.update(
            {
                "album_name": track["album"]["name"],
                "release": track["album"]["release_date"].split("-")[0],
                "album_image": track["album"]["images"][0]["url"],
                "artists": [artist["name"] for artist in track["artists"]],
                "artist": track["artists"][0]["name"],
                "title": track["name"],
                # Extract additional data as needed
            }
        )

        artist_data = session.artist(track["artists"][0]["external_urls"]["spotify"])
        info["genre"] = artist_data.get("genres", [])

        album_image_url = track["album"]["images"][0]["url"]
        image_response = requests.get(album_image_url)
        if image_response.status_code == 200:
            image_path = os.path.join(
                settings.MEDIA_ROOT, f"tmp_{randint(10000, 99999)}.png"
            )
            with open(image_path, "wb") as f:
                f.write(image_response.content)
            info["album_image_path"] = image_path

    except Exception:
        return info

    return info


def search_yandex(name: str):
    client = yandex_login()
    res = client.search(name, type_="track")
    info = {
        "album_name": "",
        "release": "",
        "artists": [],
        "title": "",
        "genre": "",
    }

    if res.tracks is None:
        return info

    if not res.tracks.results:
        return info

    track = res.tracks.results[0]

    info["album_name"] = track.albums[0].title if track.albums else ""
    info["release"] = track.albums[0].year if track.albums else ""
    info["artists"] = [artist.name for artist in track.artists]
    info["title"] = track.title

    # try to get genre
    if track.albums and track.albums[0].genre:
        genre = track.albums[0].genre
    elif track.artists and track.artists[0].genres:
        genre = track.artists[0].genres[0]
    else:
        genre = None

    info["genre"] = genre

    if track.albums and track.albums[0].cover_uri:
        cover_uri = track.albums[0].cover_uri.replace("%%", "500x500")
        image_response = requests.get("https://" + cover_uri)
        if image_response.status_code == 200:
            image_path = os.path.join(
                settings.MEDIA_ROOT, f"tmp_{randint(10000, 99999)}.png"
            )
            with open(image_path, "wb") as f:
                f.write(image_response.content)
            info["album_image_path"] = image_path

    return info


def get_spotify_album_info(album_name: str, session: spotipy.Spotify):
    search_result = session.search(q="album:" + album_name, type="album")
    albums = search_result.get("albums", {}).get("items", [])
    if albums:
        return albums[0]
    return None


def get_spotify_artist_info(artist_name: str, session: spotipy.Spotify):
    search_result = session.search(q="artist:" + artist_name, type="artist")
    artists = search_result.get("artists", {}).get("items", [])
    if artists:
        return artists[0]
    return None


def get_yandex_album_info(album_name: str, client: Client):
    search = client.search(album_name, type_="album")
    if search.albums:
        return search.albums.results[0]
    return None


def get_yandex_artist_info(artist_name: str, client: Client):
    search = client.search(artist_name, type_="artist")
    if search.artists:
        return search.artists.results[0]
    return None


def download_image(url, save_path):
    image_path = os.path.join(save_path, f"tmp_{randint(10000, 99999)}.png")
    if type(url) is Cover:
        url.download(image_path)
    else:
        if not url.startswith("http"):
            url = "https://" + url
        response = requests.get(url)
        if response.status_code == 200:
            with open(image_path, "wb") as f:
                f.write(response.content)
            return image_path
    return ""


def update_album_info(album: AlbumModel, author_name: str = None) -> None:
    client = yandex_login()
    spotify_session = create_spotify_session()

    if author_name:
        yandex_album_info = get_yandex_album_info(
            album.name + " - " + author_name, client
        )
        spotify_album_info = get_spotify_album_info(
            album.name + " - " + author_name, spotify_session
        )
    else:
        yandex_album_info = get_yandex_album_info(album.name, client)
        spotify_album_info = get_spotify_album_info(album.name, spotify_session)

    # Combine and prioritize Spotify data
    album_data = {}
    if yandex_album_info:
        album_data.update(
            {
                "name": album_data.get("name", yandex_album_info.title),
                "genre": album_data.get("genre", yandex_album_info.genre),
                "description": yandex_album_info.description,
                "type": yandex_album_info.type,
            }
        )

    if spotify_album_info:
        album_data = {
            "name": spotify_album_info.get("name", album.name),
            "release_date": spotify_album_info.get("release_date", ""),
            "total_tracks": spotify_album_info.get("total_tracks", ""),
            "link": spotify_album_info["external_urls"]["spotify"],
            "genre": spotify_album_info.get("genres", []),
        }

    album.meta = album_data
    album.save()

    # Handle Album Image - Prefer Spotify, fallback to Yandex
    image_path = None
    if (
        spotify_album_info
        and "images" in spotify_album_info
        and spotify_album_info["images"]
    ):
        image_path = download_image(
            spotify_album_info["images"][0]["url"], settings.MEDIA_ROOT
        )
    elif yandex_album_info and yandex_album_info.cover_uri:
        image_path = download_image(
            "https://" + yandex_album_info.cover_uri, settings.MEDIA_ROOT
        )

    generated_name = slugify(
        GoogleTranslator(source="auto", target="en").translate(
            album.name,
            target_language="en",
        )
    )

    if image_path:
        with open(image_path, "rb") as f:
            album.image.save(
                generated_name + ".png",
                File(
                    f,
                    name=generated_name + ".png",
                ),
                save=True,
            )
        os.remove(image_path)
        album.save()

    # Update Album Authors from Spotify data if available
    if spotify_album_info and "artists" in spotify_album_info:
        album_authors = []
        for artist in spotify_album_info["artists"]:
            author, created = Author.objects.get_or_create(name=artist["name"])
            album_authors.append(author)
        album.authors.set(album_authors)

    if generated_name and not AlbumModel.objects.filter(slug=generated_name).exists():
        if len(generated_name) > 20:
            generated_name = generated_name.split("-")[0]
            if len(generated_name) > 20:
                generated_name = generated_name[:20]
            if not AlbumModel.objects.filter(slug=generated_name).exists():
                album.slug = generated_name
                album.save()
            else:
                album.slug = generated_name[:14] + "_" + generate_charset(5)
                album.save()
        else:
            album.slug = generated_name
            album.save()


def update_author_info(author: Author) -> None:
    client = yandex_login()
    spotify_session = create_spotify_session()

    # Retrieve info from both services
    yandex_artist_info = get_yandex_artist_info(author.name, client)
    spotify_artist_info = get_spotify_artist_info(author.name, spotify_session)

    # Combine and prioritize Spotify data
    author_data = {}
    if yandex_artist_info:
        author_data.update(
            {
                "name": author_data.get("name", yandex_artist_info.name),
                "genres": author_data.get("genres", yandex_artist_info.genres),
                "description": yandex_artist_info.description,
            }
        )

    if spotify_artist_info:
        author_data = {
            "name": spotify_artist_info.get("name", author.name),
            "genres": spotify_artist_info.get("genres", []),
            "popularity": spotify_artist_info.get("popularity", 0),
            "link": spotify_artist_info["external_urls"]["spotify"],
        }

    author.meta = author_data
    author.save()

    # Handle Author Image - Prefer Spotify, fallback to Yandex
    image_path = None
    if (
        spotify_artist_info
        and "images" in spotify_artist_info
        and spotify_artist_info["images"]
    ):
        image_path = download_image(
            spotify_artist_info["images"][0]["url"], settings.MEDIA_ROOT
        )
    elif yandex_artist_info and yandex_artist_info.cover:
        image_path = download_image(yandex_artist_info.cover, settings.MEDIA_ROOT)

    generated_name = slugify(
        GoogleTranslator(source="auto", target="en").translate(
            author.name,
            target_language="en",
        )
    )
    if image_path:
        with open(image_path, "rb") as f:
            author.image.save(
                generated_name + ".png",
                File(f, name=generated_name + ".png"),
                save=True,
            )
        os.remove(image_path)
        author.save()

    if generated_name and not Author.objects.filter(slug=generated_name).exists():
        if len(generated_name) > 20:
            generated_name = generated_name.split("-")[0]
            if len(generated_name) > 20:
                generated_name = generated_name[:20]
            if not Author.objects.filter(slug=generated_name).exists():
                author.slug = generated_name
                author.save()
            else:
                author.slug = generated_name[:14] + "_" + generate_charset(5)
                author.save()
        else:
            author.slug = generated_name
            author.save()


def search_all_platforms(track_name: str) -> dict:
    session = spotipy.Spotify(
        auth_manager=spotipy.SpotifyClientCredentials(
            client_id=settings.MUSIC_SPOTIFY_ID,
            client_secret=settings.MUSIC_SPOTIFY_SECRET,
        )
    )
    spotify_info = get_spotify_info(track_name, session)
    yandex_info = search_yandex(track_name)
    if "album_image_path" in spotify_info and "album_image_path" in yandex_info:
        os.remove(yandex_info["album_image_path"])

    combined_artists = set()
    for artist in spotify_info.get("artists", []) + yandex_info.get("artists", []):
        normalized_artist = normalize_text(artist)
        if not any(
            is_similar_artist(normalized_artist, existing_artist)
            for existing_artist in combined_artists
        ):
            combined_artists.add(normalized_artist)

    genre = spotify_info.get("genre") or yandex_info.get("genre")
    if type(genre) is list:
        genre = sorted(genre, key=lambda x: len(x))
        genre = genre[0]

    track_info = {
        "album_name": spotify_info.get("album_name")
        or yandex_info.get("album_name", ""),
        "release": spotify_info.get("release") or yandex_info.get("release", ""),
        "artists": list(combined_artists),
        "title": spotify_info.get("title") or yandex_info.get("title", ""),
        "genre": genre,
        "album_image": spotify_info.get("album_image_path")
        or yandex_info.get("album_image_path", None),
    }

    return track_info
