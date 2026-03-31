import os
import re
from random import randint
from typing import Any

import requests
import structlog

from akarpov.music.services.external import (
    ExternalServiceClient,
    external_service_fallback,
)

try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None

from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.db.models import Model
from django.utils.text import slugify

from akarpov.music.models import Album as AlbumModel
from akarpov.music.models import Author
from akarpov.utils.generators import generate_charset
from akarpov.utils.text import is_similar_artist, normalize_text

logger = structlog.get_logger(__name__)


def clean_name(name: str) -> str:
    cleaned = name.strip().replace(" ", "_")
    cleaned = re.sub(r"[^\w\-]", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    cleaned = cleaned.strip("_")
    return cleaned


def split_authors(authors_str: str) -> list[str]:
    if not authors_str:
        return []
    authors = []
    for part in re.split(r"[,/&]", authors_str):
        cleaned = part.strip()
        if " feat." in cleaned.lower():
            main_artist, feat_artist = cleaned.lower().split(" feat.", 1)
            authors.extend([main_artist.strip(), feat_artist.strip()])
        elif " ft." in cleaned.lower():
            main_artist, feat_artist = cleaned.lower().split(" ft.", 1)
            authors.extend([main_artist.strip(), feat_artist.strip()])
        elif " x " in cleaned:
            authors.extend(p.strip() for p in cleaned.split(" x "))
        elif cleaned:
            authors.append(cleaned)
    seen = set()
    return [x for x in authors if not (x in seen or seen.add(x))]


@external_service_fallback
def safe_translate(text: str) -> str:
    try:
        text = clean_name(text)
        if GoogleTranslator:
            try:
                translated = GoogleTranslator(source="auto", target="en").translate(
                    text
                )
                result = slugify(translated).replace("-", "_")
                if result and len(result) > 2:
                    return result.lower()
            except Exception:
                pass
        result = slugify(text).replace("-", "_")
        return result.lower() if result else text.lower().replace(" ", "_")
    except Exception:
        return (
            slugify(clean_name(text)).replace("-", "_").lower() if text else "unknown"
        )


def generate_readable_slug(name: str, model: Model) -> str:
    slug = safe_translate(name)
    slug = clean_name(slug)

    if not slug or len(slug) < 3:
        slug = slugify(name).replace("-", "_")

    if not slug or len(slug) < 3:
        slug = re.sub(r"[^\w\s-]", "", name.lower())
        slug = re.sub(r"[\s_-]+", "_", slug).strip("_")

    if not slug:
        slug = "item_" + generate_charset(5)

    if len(slug) > 20:
        truncated = slug[:20].rsplit("_", 1)[0]
        slug = truncated if truncated else slug[:20]

    original_slug = slug.lower()
    counter = 1
    while model.objects.filter(slug__iexact=slug).exists():
        if len(original_slug) > 14:
            truncated = original_slug[:14].rsplit("_", 1)[0]
            base_slug = truncated if truncated else original_slug[:14]
        else:
            base_slug = original_slug
        suffix = f"_{generate_charset(5)}" if counter == 1 else f"_{counter}"
        slug = f"{base_slug}{suffix}"
        counter += 1
        if counter > 100:
            slug = f"{base_slug}_{generate_charset(8)}"
            break
    return slug.lower()


def _get_default_proxy():
    from akarpov.music.models import DownloadConfig

    config = DownloadConfig.get_default()
    if config and config.proxy_url:
        return {"http": config.proxy_url, "https": config.proxy_url}
    proxy = os.environ.get("MUSIC_PROXY_URL", "")
    if proxy:
        return {"http": proxy, "https": proxy}
    return None


def _create_spotify_session_safe():
    try:
        import spotipy
        from spotipy import SpotifyClientCredentials

        cid = getattr(settings, "MUSIC_SPOTIFY_ID", "")
        secret = getattr(settings, "MUSIC_SPOTIFY_SECRET", "")
        if not cid or not secret:
            return None
        proxies = _get_default_proxy()

        session = requests.Session()
        if proxies:
            session.proxies = proxies
        session.timeout = 30

        return spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=cid,
                client_secret=secret,
                proxies=proxies,
            ),
            retries=0,
            requests_timeout=30,
            proxies=proxies,
            requests_session=session,
        )
    except Exception as e:
        logger.warning("Failed to create Spotify session", error=str(e))
        return None


def create_spotify_session():
    import spotipy
    from spotipy import SpotifyClientCredentials

    if not settings.MUSIC_SPOTIFY_ID or not settings.MUSIC_SPOTIFY_SECRET:
        raise ConnectionError("No spotify credentials provided")
    proxies = _get_default_proxy()

    session = requests.Session()
    if proxies:
        session.proxies = proxies
    session.timeout = 30

    return spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=settings.MUSIC_SPOTIFY_ID,
            client_secret=settings.MUSIC_SPOTIFY_SECRET,
            proxies=proxies,
        ),
        proxies=proxies,
        requests_session=session,
    )


def _yandex_login_safe():
    try:
        from yandex_music import Client

        token = getattr(settings, "MUSIC_YANDEX_TOKEN", "")
        if not token:
            return None
        return Client(token).init()
    except Exception as e:
        logger.warning("Failed to create Yandex session", error=str(e))
        return None


def yandex_login():
    from yandex_music import Client

    if not settings.MUSIC_YANDEX_TOKEN:
        raise ConnectionError("No yandex credentials provided")
    return Client(settings.MUSIC_YANDEX_TOKEN).init()


def spotify_search(name: str, session, search_type="track"):
    res = session.search(name, type=search_type)
    return res


def clean_spotify_response(data: dict[str, Any]) -> dict[str, Any]:
    if isinstance(data, dict):
        return {
            k: clean_spotify_response(v)
            for k, v in data.items()
            if k != "available_markets"
        }
    elif isinstance(data, list):
        return [clean_spotify_response(item) for item in data]
    return data


@external_service_fallback
def get_spotify_info(name: str, session) -> dict:
    info = {
        "album_name": "",
        "album_image": "",
        "release": "",
        "artists": [],
        "artist": "",
        "title": "",
        "genre": [],
        "meta": {},
        "album_meta": {},
        "external_urls": {},
        "full_data": {},
    }

    try:
        results = spotify_search(name, session)["tracks"]["items"]
        if not results:
            return info

        track = results[0]
        artist_data = session.artist(track["artists"][0]["external_urls"]["spotify"])
        album_data = session.album(track["album"]["id"])

        info.update(
            {
                "album_name": track["album"]["name"],
                "album_image": track["album"]["images"][0]["url"]
                if track["album"]["images"]
                else "",
                "release": track["album"]["release_date"].split("-")[0]
                if track["album"].get("release_date")
                else "",
                "artists": [artist["name"] for artist in track["artists"]],
                "artist": track["artists"][0]["name"],
                "title": track["name"],
                "genre": artist_data.get("genres", []),
                "meta": {
                    "duration_ms": track.get("duration_ms"),
                    "explicit": track.get("explicit"),
                    "preview_url": track.get("preview_url"),
                    "track_number": track.get("track_number"),
                    "type": track.get("type"),
                },
                "album_meta": clean_spotify_response(album_data),
                "external_urls": track.get("external_urls", {}),
                "full_data": clean_spotify_response(track),
            }
        )

        if track["album"]["images"]:
            album_image_url = track["album"]["images"][0]["url"]
            image_response = requests.get(album_image_url, timeout=15)
            if image_response.status_code == 200:
                image_path = os.path.join(
                    settings.MEDIA_ROOT, f"tmp_{randint(10000, 99999)}.png"
                )
                with open(image_path, "wb") as f:
                    f.write(image_response.content)
                info["album_image_path"] = image_path

    except Exception as e:
        logger.warning("Failed to get Spotify info", error=str(e))

    return info


def search_yandex(name: str):
    info = {
        "album_name": "",
        "release": "",
        "artists": [],
        "title": "",
        "genre": "",
    }
    client = _yandex_login_safe()
    if not client:
        return info

    try:
        res = client.search(name, type_="track")
        if res.tracks is None or not res.tracks.results:
            return info

        track = res.tracks.results[0]
        info["album_name"] = track.albums[0].title if track.albums else ""
        info["release"] = track.albums[0].year if track.albums else ""
        info["artists"] = [artist.name for artist in track.artists]
        info["title"] = track.title

        if track.albums and track.albums[0].genre:
            genre = track.albums[0].genre
        elif track.artists and track.artists[0].genres:
            genre = track.artists[0].genres[0]
        else:
            genre = None
        info["genre"] = genre

        if track.albums and track.albums[0].cover_uri:
            cover_uri = track.albums[0].cover_uri.replace("%%", "500x500")
            image_response = requests.get("https://" + cover_uri, timeout=15)
            if image_response.status_code == 200:
                image_path = os.path.join(
                    settings.MEDIA_ROOT, f"tmp_{randint(10000, 99999)}.png"
                )
                with open(image_path, "wb") as f:
                    f.write(image_response.content)
                info["album_image_path"] = image_path
    except Exception as e:
        logger.warning("Failed to search Yandex", error=str(e))

    return info


@external_service_fallback
def get_spotify_album_info(album_name: str, session) -> dict:
    info = {
        "name": "",
        "link": "",
        "meta": {},
        "image_url": "",
        "release_date": "",
        "total_tracks": 0,
        "images": [],
        "external_urls": {},
        "artists": [],
        "genres": [],
        "tracks": [],
        "full_data": {},
    }
    try:
        search_result = session.search(q="album:" + album_name, type="album")
        albums = search_result.get("albums", {}).get("items", [])
        if not albums:
            return info
        album = albums[0]
        album_id = album["id"]
        full_album = session.album(album_id)
        tracks = session.album_tracks(album_id)
        return {
            "name": album.get("name", ""),
            "link": album.get("external_urls", {}).get("spotify", ""),
            "meta": {
                "album_type": album.get("album_type", ""),
                "release_date_precision": album.get("release_date_precision", ""),
                "total_tracks": album.get("total_tracks", 0),
                "type": album.get("type", ""),
            },
            "image_url": next(
                (img["url"] for img in album.get("images", []) if img.get("url")), ""
            ),
            "release_date": album.get("release_date", ""),
            "total_tracks": album.get("total_tracks", 0),
            "images": album.get("images", []),
            "external_urls": album.get("external_urls", {}),
            "artists": clean_spotify_response(album.get("artists", [])),
            "genres": clean_spotify_response(full_album.get("genres", [])),
            "tracks": clean_spotify_response(tracks.get("items", [])),
            "full_data": clean_spotify_response(full_album),
        }
    except Exception as e:
        logger.warning("Failed to get album info", error=str(e))
        return info


@external_service_fallback
def get_spotify_artist_info(artist_name: str, session) -> dict:
    info = {
        "name": "",
        "link": "",
        "meta": {},
        "image_url": "",
        "genres": [],
        "popularity": 0,
        "images": [],
        "external_urls": {},
        "full_data": {},
    }
    try:
        search_result = session.search(q="artist:" + artist_name, type="artist")
        artists = search_result.get("artists", {}).get("items", [])
        if not artists:
            return info
        artist = artists[0]
        return {
            "name": artist.get("name", ""),
            "link": artist.get("external_urls", {}).get("spotify", ""),
            "meta": {
                "type": artist.get("type", ""),
            },
            "image_url": next(
                (img["url"] for img in artist.get("images", []) if img.get("url")), ""
            ),
            "genres": artist.get("genres", []),
            "images": artist.get("images", []),
            "external_urls": artist.get("external_urls", {}),
            "full_data": clean_spotify_response(artist),
        }
    except Exception as e:
        logger.warning("Failed to get artist info", error=str(e))
        return info


def get_yandex_album_info(album_name: str, client):
    search = client.search(album_name, type_="album")
    if search.albums:
        return search.albums.results[0]
    return None


def get_yandex_artist_info(artist_name: str, client):
    search = client.search(artist_name, type_="artist")
    if search.artists:
        return search.artists.results[0]
    return None


def download_image(url, save_path):
    from yandex_music import Cover

    image_path = os.path.join(save_path, f"tmp_{randint(10000, 99999)}.png")
    try:
        if isinstance(url, Cover):
            url.download(image_path)
        else:
            if not url.startswith("http"):
                url = "https://" + url
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(response.content)
                return image_path
    except Exception as e:
        logger.warning("Failed to download image", error=str(e), url=str(url))
    return ""


def _get_api_info_safe(api_func, search_term, session):
    if session is None:
        return None
    try:
        return api_func(search_term, session)
    except Exception as e:
        logger.warning(f"API call {api_func.__name__} failed", error=str(e))
        return None


def update_album_info(album: AlbumModel, author_name: str = None) -> None:
    try:
        _update_album_info_impl(album, author_name)
    except Exception as e:
        logger.error("update_album_info failed", album_id=album.id, error=str(e))


def _update_album_info_impl(album: AlbumModel, author_name: str = None) -> None:
    client = _yandex_login_safe()
    spotify_session = _create_spotify_session_safe()

    search_term = f"{album.name} - {author_name}" if author_name else album.name

    yandex_album_info = _get_api_info_safe(get_yandex_album_info, search_term, client)
    spotify_album_info = _get_api_info_safe(
        get_spotify_album_info, search_term, spotify_session
    )

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
                "name": album_data.get("name")
                or getattr(yandex_album_info, "title", ""),
                "genre": album_data.get("genre")
                or getattr(yandex_album_info, "genre", None),
                "description": getattr(yandex_album_info, "description", ""),
                "type": getattr(yandex_album_info, "type", ""),
            }
        )

    album.meta = album_data
    album.save(update_fields=["meta"])

    image_path = _get_album_image(spotify_album_info, yandex_album_info)
    if image_path:
        _save_model_image(album, image_path)

    if spotify_album_info and "artists" in spotify_album_info:
        _update_album_authors(album, spotify_album_info["artists"])

    new_slug = generate_readable_slug(album.name, AlbumModel)
    if new_slug != album.slug:
        album.slug = new_slug
        album.save(update_fields=["slug"])


def _get_album_image(spotify_info, yandex_info):
    if spotify_info and "images" in spotify_info and spotify_info["images"]:
        return download_image(spotify_info["images"][0]["url"], settings.MEDIA_ROOT)
    elif yandex_info and getattr(yandex_info, "cover_uri", None):
        return download_image("https://" + yandex_info.cover_uri, settings.MEDIA_ROOT)
    return None


def _save_model_image(obj, image_path):
    if not image_path or not os.path.exists(image_path):
        return
    try:
        generated_name = safe_translate(obj.name)
        with open(image_path, "rb") as f:
            obj.image.save(
                generated_name + ".png",
                File(f, name=generated_name + ".png"),
                save=True,
            )
        os.remove(image_path)
    except Exception as e:
        logger.error("Error saving image", error=str(e))
        if os.path.exists(image_path):
            os.remove(image_path)


def _update_album_authors(album, artists):
    album_authors = []
    for artist in artists:
        author, _ = Author.objects.get_or_create(name=artist["name"])
        album_authors.append(author)
    album.authors.set(album_authors)


def update_author_info(author: Author) -> None:
    try:
        _update_author_info_impl(author)
    except Exception as e:
        logger.error("update_author_info failed", author_id=author.id, error=str(e))


def _update_author_info_impl(author: Author) -> None:
    client = _yandex_login_safe()
    spotify_session = _create_spotify_session_safe()

    yandex_artist_info = _get_api_info_safe(get_yandex_artist_info, author.name, client)
    spotify_artist_info = _get_api_info_safe(
        get_spotify_artist_info, author.name, spotify_session
    )

    author_data = {}
    if spotify_artist_info:
        author_data = {
            "name": spotify_artist_info.get("name", author.name),
            "genres": spotify_artist_info.get("genres", []),
            "popularity": spotify_artist_info.get("popularity", 0),
            "link": spotify_artist_info.get("external_urls", {}).get("spotify", ""),
        }
    if yandex_artist_info:
        author_data.update(
            {
                "name": author_data.get("name")
                or getattr(yandex_artist_info, "name", ""),
                "genres": author_data.get("genres")
                or getattr(yandex_artist_info, "genres", []),
                "description": getattr(yandex_artist_info, "description", ""),
            }
        )

    with transaction.atomic():
        author.meta = author_data
        author.save(update_fields=["meta"])

    image_path = _get_author_image(spotify_artist_info, yandex_artist_info)
    if image_path:
        _save_model_image(author, image_path)

    new_slug = generate_readable_slug(author.name, Author)
    if new_slug != author.slug:
        with transaction.atomic():
            author.slug = new_slug
            author.save(update_fields=["slug"])


def _get_author_image(spotify_info, yandex_info):
    if spotify_info and "images" in spotify_info and spotify_info["images"]:
        return download_image(spotify_info["images"][0]["url"], settings.MEDIA_ROOT)
    elif yandex_info and getattr(yandex_info, "cover", None):
        return download_image(yandex_info.cover, settings.MEDIA_ROOT)
    return None


def search_all_platforms(track_name: str) -> dict:
    empty_result = {
        "album_name": "",
        "release": "",
        "artists": [],
        "title": "",
        "genre": None,
        "album_image": None,
    }

    if not track_name or not track_name.strip():
        return empty_result

    logger.debug("search_all_platforms", query=track_name)

    spotify_info = {}
    if settings.MUSIC_EXTERNAL_SERVICE_URL:
        try:
            client = ExternalServiceClient()
            spotify_info = client.get_spotify_info(track_name) or {}
        except Exception as e:
            logger.warning("External service failed", error=str(e))
    else:
        session = _create_spotify_session_safe()
        if session:
            try:
                spotify_info = get_spotify_info(track_name, session)
            except Exception as e:
                logger.warning("Spotify search failed", error=str(e))

    yandex_info = {}
    try:
        yandex_info = search_yandex(track_name)
    except Exception as e:
        logger.warning("Yandex search failed", error=str(e))

    if "album_image_path" in spotify_info and "album_image_path" in yandex_info:
        try:
            os.remove(yandex_info["album_image_path"])
        except OSError:
            pass

    combined_artists = set()
    for artist in spotify_info.get("artists", []) + yandex_info.get("artists", []):
        normalized_artist = normalize_text(artist)
        if not any(
            is_similar_artist(normalized_artist, existing_artist)
            for existing_artist in combined_artists
        ):
            combined_artists.add(normalized_artist)

    genre = spotify_info.get("genre") or yandex_info.get("genre")
    if isinstance(genre, list) and genre:
        genre = sorted(genre, key=len)[0]

    return {
        "album_name": spotify_info.get("album_name")
        or yandex_info.get("album_name", ""),
        "release": spotify_info.get("release") or yandex_info.get("release", ""),
        "artists": list(combined_artists),
        "title": spotify_info.get("title") or yandex_info.get("title", ""),
        "genre": genre,
        "album_image": spotify_info.get("album_image_path")
        or yandex_info.get("album_image_path", None),
    }
