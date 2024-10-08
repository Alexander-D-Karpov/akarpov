import os
from random import randint

import requests
import spotipy

try:
    from deep_translator import GoogleTranslator
except requests.exceptions.JSONDecodeError:
    print("Failed to initialize GoogleTranslator due to external API issues.")
from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.db.models import Model
from django.utils.text import slugify
from spotipy import SpotifyClientCredentials
from yandex_music import Client, Cover

from akarpov.music.models import Album as AlbumModel
from akarpov.music.models import Author
from akarpov.utils.generators import generate_charset
from akarpov.utils.text import is_similar_artist, normalize_text


def generate_readable_slug(name: str, model: Model) -> str:
    # Translate and slugify the name
    slug = safe_translate(name)

    # Truncate slug if it's too long
    if len(slug) > 20:
        slug = slug[:20]
        last_dash = slug.rfind("-")
        if last_dash != -1:
            slug = slug[:last_dash]

    original_slug = slug

    # Ensure uniqueness
    counter = 1
    while model.objects.filter(slug=slug).exists():
        if len(original_slug) > 14:
            truncated_slug = original_slug[:14]
            last_dash = truncated_slug.rfind("-")
            if last_dash != -1:
                truncated_slug = truncated_slug[:last_dash]
        else:
            truncated_slug = original_slug

        suffix = f"_{generate_charset(5)}" if counter == 1 else f"_{counter}"
        slug = f"{truncated_slug}{suffix}"
        counter += 1

    return slug


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

    search_term = f"{album.name} - {author_name}" if author_name else album.name

    yandex_album_info = get_api_info(get_yandex_album_info, search_term, client)
    spotify_album_info = get_api_info(
        get_spotify_album_info, search_term, spotify_session
    )

    # Combine and prioritize Spotify data
    album_data = {}

    if spotify_album_info:
        album_data = {
            "name": spotify_album_info.get("name", album.name),
            "release_date": spotify_album_info.get("release_date", ""),
            "total_tracks": spotify_album_info.get("total_tracks", ""),
            "link": spotify_album_info.get("external_urls", {}).get("spotify", ""),
            "genre": spotify_album_info.get("genres", []),
        }
    if yandex_album_info:
        album_data.update(
            {
                "name": album_data.get("name") or yandex_album_info.title,
                "genre": album_data.get("genre") or yandex_album_info.genre,
                "description": yandex_album_info.description,
                "type": yandex_album_info.type,
            }
        )

    album.meta = album_data
    album.save()

    # Handle Album Image - Prefer Spotify, fallback to Yandex
    image_path = get_album_image(spotify_album_info, yandex_album_info)

    if image_path:
        save_album_image(album, image_path)

    # Update Album Authors from Spotify data if available
    if spotify_album_info and "artists" in spotify_album_info:
        update_album_authors(album, spotify_album_info["artists"])

    album.slug = generate_readable_slug(album.name, AlbumModel)
    album.save()


def get_album_image(spotify_info, yandex_info):
    if spotify_info and "images" in spotify_info and spotify_info["images"]:
        return download_image(spotify_info["images"][0]["url"], settings.MEDIA_ROOT)
    elif yandex_info and yandex_info.cover_uri:
        return download_image("https://" + yandex_info.cover_uri, settings.MEDIA_ROOT)
    return None


def save_album_image(album, image_path):
    if not image_path:
        return

    try:
        generated_name = safe_translate(album.name)
        with open(image_path, "rb") as f:
            album.image.save(
                generated_name + ".png",
                File(f, name=generated_name + ".png"),
                save=True,
            )
        os.remove(image_path)
        album.save()
    except Exception as e:
        print(f"Error saving album image: {str(e)}")


def update_album_authors(album, artists):
    album_authors = []
    for artist in artists:
        author, created = Author.objects.get_or_create(name=artist["name"])
        album_authors.append(author)
    album.authors.set(album_authors)


def update_author_info(author: Author) -> None:
    client = yandex_login()
    spotify_session = create_spotify_session()

    yandex_artist_info = get_api_info(get_yandex_artist_info, author.name, client)
    spotify_artist_info = get_api_info(
        get_spotify_artist_info, author.name, spotify_session
    )

    author_data = combine_artist_data(author, spotify_artist_info, yandex_artist_info)

    with transaction.atomic():
        author.meta = author_data
        author.save()

    image_path = get_author_image(spotify_artist_info, yandex_artist_info)

    if image_path:
        save_author_image(author, image_path)

    author.slug = generate_readable_slug(author.name, Author)
    with transaction.atomic():
        author.save()


def get_api_info(api_func, search_term, session):
    try:
        return api_func(search_term, session)
    except Exception as e:
        print(f"Error fetching info from {api_func.__name__}: {str(e)}")
        return None


def combine_artist_data(author, spotify_info, yandex_info):
    author_data = {}
    if spotify_info:
        author_data = {
            "name": spotify_info.get("name", author.name),
            "genres": spotify_info.get("genres", []),
            "popularity": spotify_info.get("popularity", 0),
            "link": spotify_info.get("external_urls", {}).get("spotify", ""),
        }
    if yandex_info:
        author_data.update(
            {
                "name": author_data.get("name") or yandex_info.name,
                "genres": author_data.get("genres") or yandex_info.genres,
                "description": yandex_info.description,
            }
        )
    return author_data


def get_author_image(spotify_info, yandex_info):
    if spotify_info and "images" in spotify_info and spotify_info["images"]:
        return download_image(spotify_info["images"][0]["url"], settings.MEDIA_ROOT)
    elif yandex_info and yandex_info.cover:
        return download_image(yandex_info.cover, settings.MEDIA_ROOT)
    return None


def save_author_image(author, image_path):
    if not image_path:
        return

    try:
        generated_name = safe_translate(author.name)
        with open(image_path, "rb") as f:
            author.image.save(
                generated_name + ".png",
                File(f, name=generated_name + ".png"),
                save=True,
            )
        os.remove(image_path)
        author.save()
    except Exception as e:
        print(f"Error saving author image: {str(e)}")


def safe_translate(text):
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        return slugify(translated)
    except Exception as e:
        print(f"Error translating text: {str(e)}")
        return slugify(text)


def search_all_platforms(track_name: str) -> dict:
    print(track_name)
    # session = spotipy.Spotify(
    #     auth_manager=spotipy.SpotifyClientCredentials(
    #         client_id=settings.MUSIC_SPOTIFY_ID,
    #         client_secret=settings.MUSIC_SPOTIFY_SECRET,
    #     )
    # )
    # spotify_info = get_spotify_info(track_name, session)
    spotify_info = {}  # TODO: add proxy for info retrieve
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
