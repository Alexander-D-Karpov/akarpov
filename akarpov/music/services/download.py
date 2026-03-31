import json as json_module
import os
import re
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass, field

import requests
import spotipy
import structlog
import yt_dlp
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.cache import cache
from spotipy import SpotifyClientCredentials
from ytmusicapi import YTMusic

from akarpov.music.models import DownloadConfig, DownloadJob, DownloadTrack

logger = structlog.get_logger(__name__)

SPOTIFY_RATE_LIMIT_KEY = "spotify_rate_limited"
SPOTIFY_RATE_LIMIT_TTL = 25 * 3600


@dataclass
class TrackMeta:
    name: str = ""
    artists: list = field(default_factory=list)
    album: str = ""
    duration_ms: int = 0
    spotify_url: str = ""
    genre: str = ""
    release: str = ""
    explicit: bool = False
    album_image_url: str = ""
    lyrics: str = ""


@dataclass
class ResolveResult:
    tracks: list = field(default_factory=list)
    playlist_name: str = ""
    is_playlist: bool = False


class ConfigProvider:
    def __init__(self, config: DownloadConfig = None):
        self._config = config

    @property
    def spotify_client_id(self):
        if self._config and self._config.spotify_client_id:
            return self._config.spotify_client_id
        return getattr(settings, "MUSIC_SPOTIFY_ID", "")

    @property
    def spotify_client_secret(self):
        if self._config and self._config.spotify_client_secret:
            return self._config.spotify_client_secret
        return getattr(settings, "MUSIC_SPOTIFY_SECRET", "")

    @property
    def proxy_url(self):
        if self._config and self._config.proxy_url:
            return self._config.proxy_url
        return os.environ.get("MUSIC_PROXY_URL", "")

    @property
    def soundcloud_client_id(self):
        if self._config and self._config.soundcloud_client_id:
            return self._config.soundcloud_client_id
        return ""

    def get_youtube_cookie_file(self):
        if self._config and self._config.youtube_cookies:
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
            tmp.write(self._config.youtube_cookies)
            tmp.flush()
            tmp.close()
            return tmp.name
        return CookieManager.get_temp_cookie_file()


class CookieManager:
    _lock = threading.Lock()

    @staticmethod
    def get_cookie_path():
        return getattr(settings, "YOUTUBE_COOKIE_PATH", None)

    @classmethod
    def get_temp_cookie_file(cls):
        master = cls.get_cookie_path()
        if not master or not os.path.exists(master):
            return None
        with cls._lock:
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
            shutil.copy2(master, tmp.name)
            return tmp.name

    @staticmethod
    def save_cookies(content: str):
        path = CookieManager.get_cookie_path()
        if not path:
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        os.chmod(path, 0o600)

    @staticmethod
    def cookies_exist():
        path = CookieManager.get_cookie_path()
        return path and os.path.exists(path) and os.path.getsize(path) > 0

    @staticmethod
    def get_cookies_info():
        path = CookieManager.get_cookie_path()
        if not path or not os.path.exists(path):
            return None
        stat = os.stat(path)
        return {"path": path, "size": stat.st_size, "modified": stat.st_mtime}


def is_spotify_rate_limited():
    return cache.get(SPOTIFY_RATE_LIMIT_KEY, False)


def set_spotify_rate_limited():
    cache.set(SPOTIFY_RATE_LIMIT_KEY, True, SPOTIFY_RATE_LIMIT_TTL)
    logger.warning("Spotify rate limited — blocking for 25h")


def clear_spotify_rate_limit():
    cache.delete(SPOTIFY_RATE_LIMIT_KEY)


class SpotifyRateLimitError(Exception):
    pass


def create_spotify_session(provider: ConfigProvider = None):
    provider = provider or ConfigProvider()
    if not provider.spotify_client_id or not provider.spotify_client_secret:
        raise ConnectionError("No Spotify credentials")

    proxies = None
    if provider.proxy_url:
        proxies = {"http": provider.proxy_url, "https": provider.proxy_url}

    session = requests.Session()
    if proxies:
        session.proxies = proxies
    session.timeout = 30

    auth_manager = SpotifyClientCredentials(
        client_id=provider.spotify_client_id,
        client_secret=provider.spotify_client_secret,
        proxies=proxies,
    )

    return spotipy.Spotify(
        auth_manager=auth_manager,
        retries=0,
        requests_timeout=30,
        proxies=proxies,
        requests_session=session,
    )


def safe_spotify_call(func, *args, **kwargs):
    if is_spotify_rate_limited():
        raise SpotifyRateLimitError("Spotify is rate limited")
    try:
        return func(*args, **kwargs)
    except spotipy.SpotifyException as e:
        if e.http_status == 429:
            set_spotify_rate_limited()
            raise SpotifyRateLimitError("Spotify 429") from e
        raise


def _spotify_track_to_meta(track: dict) -> TrackMeta:
    album = track.get("album", {})
    return TrackMeta(
        name=track.get("name", ""),
        artists=[a["name"] for a in track.get("artists", [])],
        album=album.get("name", ""),
        duration_ms=track.get("duration_ms", 0),
        spotify_url=track.get("external_urls", {}).get("spotify", ""),
        release=album.get("release_date", "").split("-")[0]
        if album.get("release_date")
        else "",
        explicit=track.get("explicit", False),
        album_image_url=album["images"][0]["url"] if album.get("images") else "",
    )


def _resolve_spotify_via_api(
    url: str, provider: ConfigProvider = None
) -> ResolveResult:
    sp = create_spotify_session(provider)
    result = ResolveResult()

    if "/track/" in url:
        track = safe_spotify_call(sp.track, url)
        result.tracks.append(_spotify_track_to_meta(track))

    elif "/album/" in url:
        album = safe_spotify_call(sp.album, url)
        result.playlist_name = album["name"]
        result.is_playlist = True
        album_info = {
            "name": album["name"],
            "image": album["images"][0]["url"] if album["images"] else "",
            "release": album.get("release_date", ""),
        }
        album_tracks = safe_spotify_call(sp.album_tracks, album["id"])
        all_tracks = album_tracks.get("items", [])
        while album_tracks.get("next"):
            album_tracks = safe_spotify_call(sp.next, album_tracks)
            if album_tracks:
                all_tracks.extend(album_tracks.get("items", []))
            else:
                break
        for t in all_tracks:
            meta = _spotify_track_to_meta(t)
            meta.album = album_info["name"]
            meta.album_image_url = album_info["image"]
            meta.release = album_info.get("release", "")
            result.tracks.append(meta)

    elif "/playlist/" in url:
        playlist_meta = safe_spotify_call(sp.playlist, url)
        result.playlist_name = playlist_meta.get("name", "")
        result.is_playlist = True

        items_data = playlist_meta.get("items") or playlist_meta.get("tracks")
        if items_data is None:
            try:
                items_data = safe_spotify_call(
                    sp.playlist_items, url.split("/")[-1].split("?")[0]
                )
            except Exception:
                items_data = safe_spotify_call(
                    sp.playlist_tracks, url.split("/")[-1].split("?")[0]
                )

        while items_data:
            for item in items_data.get("items", []):
                track = item.get("item") or item.get("track")
                if track:
                    result.tracks.append(_spotify_track_to_meta(track))
            if items_data.get("next"):
                items_data = safe_spotify_call(sp.next, items_data)
            else:
                break

    elif "/artist/" in url:
        artist_id = url.split("/artist/")[1].split("?")[0]
        artist = safe_spotify_call(sp.artist, artist_id)
        result.playlist_name = f"{artist['name']} -- Discography"
        result.is_playlist = True

        albums = safe_spotify_call(
            sp.artist_albums, artist_id, album_type="album,single", limit=50
        )
        all_albums = albums.get("items", []) if albums else []
        while albums and albums.get("next"):
            albums = safe_spotify_call(sp.next, albums)
            if albums and albums.get("items"):
                all_albums.extend(albums["items"])
            else:
                break

        for album_brief in all_albums:
            try:
                full_album = safe_spotify_call(sp.album, album_brief["id"])
                if not full_album:
                    continue
                album_img = (
                    full_album["images"][0]["url"] if full_album.get("images") else ""
                )
                album_release = (
                    full_album.get("release_date", "").split("-")[0]
                    if full_album.get("release_date")
                    else ""
                )

                album_tracks = safe_spotify_call(sp.album_tracks, album_brief["id"])
                track_items = album_tracks.get("items", []) if album_tracks else []
                while album_tracks and album_tracks.get("next"):
                    album_tracks = safe_spotify_call(sp.next, album_tracks)
                    if album_tracks and album_tracks.get("items"):
                        track_items.extend(album_tracks["items"])
                    else:
                        break

                for t in track_items:
                    meta = _spotify_track_to_meta(t)
                    meta.album = full_album.get("name", "")
                    meta.album_image_url = album_img
                    meta.release = album_release
                    result.tracks.append(meta)
            except Exception as e:
                logger.warning(
                    "Failed to fetch album",
                    album_id=album_brief.get("id"),
                    error=str(e),
                )
                continue

    return result


def _resolve_spotify_via_embed(
    url: str, provider: ConfigProvider = None
) -> ResolveResult:
    provider = provider or ConfigProvider()
    result = ResolveResult()

    proxies = None
    if provider.proxy_url:
        proxies = {"http": provider.proxy_url, "https": provider.proxy_url}

    spotify_id = url.rstrip("/").split("/")[-1].split("?")[0]

    if "/track/" in url:
        meta = _scrape_embed_track(spotify_id, proxies)
        if meta:
            result.tracks.append(meta)

    elif "/album/" in url:
        tracks, album_name = _scrape_embed_album(spotify_id, proxies)
        result.tracks = tracks
        result.playlist_name = album_name
        result.is_playlist = True

    elif "/playlist/" in url:
        tracks, playlist_name = _scrape_embed_playlist(spotify_id, proxies)
        result.tracks = tracks
        result.playlist_name = playlist_name
        result.is_playlist = True

    elif "/artist/" in url:
        tracks, artist_name = _scrape_artist_discography(spotify_id, proxies)
        result.tracks = tracks
        result.playlist_name = f"{artist_name} -- Discography"
        result.is_playlist = True

    return result


_EMBED_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _fetch_embed_json(embed_url: str, proxies=None) -> dict | None:
    try:
        resp = requests.get(
            embed_url, headers=_EMBED_HEADERS, proxies=proxies, timeout=15
        )
        if resp.status_code != 200:
            logger.warning(
                "Embed fetch non-200", url=embed_url, status=resp.status_code
            )
            return None

        match = re.search(
            r'<script\s+id="__NEXT_DATA__"\s+type="application/json">\s*({.*?})\s*</script>',
            resp.text,
            re.DOTALL,
        )
        if match:
            return json_module.loads(match.group(1))

        match = re.search(
            r"Spotify\.Entity\s*=\s*({.*?});",
            resp.text,
            re.DOTALL,
        )
        if match:
            return json_module.loads(match.group(1))

        logger.warning("No JSON data found in embed page", url=embed_url)
    except Exception as e:
        logger.warning("Embed fetch failed", url=embed_url, error=str(e))
    return None


def _dig(data: dict, *keys, default=None):
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default
        if current is None:
            return default
    return current


def _scrape_embed_track(track_id: str, proxies=None) -> TrackMeta | None:
    data = _fetch_embed_json(
        f"https://open.spotify.com/embed/track/{track_id}", proxies
    )
    if not data:
        return None

    try:
        state = _dig(data, "props", "pageProps", "state", "data", "entity") or {}
        if not state:
            state = _dig(data, "props", "pageProps") or data

        name = state.get("name", "") or state.get("title", "")
        if not name:
            return None

        artists = []
        for a in state.get("artists", []):
            n = a.get("name", "") if isinstance(a, dict) else str(a)
            if n:
                artists.append(n)

        album_data = state.get("album", {}) or {}
        album_name = album_data.get("name", "") if isinstance(album_data, dict) else ""
        duration = state.get("duration_ms", 0) or state.get("duration", 0)

        images = []
        if isinstance(album_data, dict):
            images = album_data.get("images", [])
        if not images:
            cover_art = state.get("coverArt", {}) or {}
            images = cover_art.get("sources", [])
        image_url = images[0].get("url", "") if images else ""

        return TrackMeta(
            name=name,
            artists=artists if artists else ["Unknown"],
            album=album_name,
            duration_ms=int(duration) if duration else 0,
            spotify_url=f"https://open.spotify.com/track/{track_id}",
            album_image_url=image_url,
        )
    except Exception as e:
        logger.warning("Failed to parse embed track", error=str(e))
        return None


def _scrape_embed_album(album_id: str, proxies=None) -> tuple[list[TrackMeta], str]:
    data = _fetch_embed_json(
        f"https://open.spotify.com/embed/album/{album_id}", proxies
    )
    if not data:
        return [], ""

    tracks = []
    album_name = ""
    try:
        state = _dig(data, "props", "pageProps", "state", "data", "entity") or {}
        if not state:
            state = _dig(data, "props", "pageProps") or data

        album_name = state.get("name", "") or state.get("title", "")
        album_artists = [
            a.get("name", "") for a in state.get("artists", []) if isinstance(a, dict)
        ]

        images = state.get("images", [])
        if not images:
            cover_art = state.get("coverArt", {}) or {}
            images = cover_art.get("sources", [])
        image_url = images[0].get("url", "") if images else ""

        track_list = state.get("trackList", [])
        if not track_list:
            tracks_obj = state.get("tracks", {})
            if isinstance(tracks_obj, dict):
                track_list = tracks_obj.get("items", [])
            elif isinstance(tracks_obj, list):
                track_list = tracks_obj

        for t in track_list:
            t_name = (
                t.get("name", "")
                or t.get("title", "")
                or t.get("track", {}).get("name", "")
            )
            if not t_name:
                continue

            t_artists = []
            for a in t.get("artists", []):
                n = a.get("name", "") if isinstance(a, dict) else str(a)
                if n:
                    t_artists.append(n)
            if not t_artists:
                t_artists = album_artists

            t_id = (
                t.get("uid", "") or t.get("id", "") or t.get("uri", "").split(":")[-1]
            )

            meta = TrackMeta(
                name=t_name,
                artists=t_artists if t_artists else ["Unknown"],
                album=album_name,
                duration_ms=int(t.get("duration_ms", 0) or t.get("duration", 0) or 0),
                spotify_url=f"https://open.spotify.com/track/{t_id}" if t_id else "",
                album_image_url=image_url,
            )
            tracks.append(meta)
    except Exception as e:
        logger.warning("Failed to parse embed album", error=str(e))

    return tracks, album_name


def _scrape_embed_playlist(
    playlist_id: str, proxies=None
) -> tuple[list[TrackMeta], str]:
    data = _fetch_embed_json(
        f"https://open.spotify.com/embed/playlist/{playlist_id}", proxies
    )
    if not data:
        return [], ""

    tracks = []
    playlist_name = ""
    try:
        state = _dig(data, "props", "pageProps", "state", "data", "entity") or {}
        if not state:
            state = _dig(data, "props", "pageProps") or data

        playlist_name = state.get("name", "") or state.get("title", "")

        track_list = state.get("trackList", [])
        if not track_list:
            tracks_obj = state.get("tracks", {})
            if isinstance(tracks_obj, dict):
                track_list = tracks_obj.get("items", [])
            elif isinstance(tracks_obj, list):
                track_list = tracks_obj

        for t in track_list:
            track_data = t
            if "track" in t and isinstance(t["track"], dict):
                track_data = t["track"]
            if "item" in t and isinstance(t["item"], dict):
                track_data = t["item"]

            t_name = track_data.get("name", "") or track_data.get("title", "")
            if not t_name:
                continue

            t_artists = []
            for a in track_data.get("artists", []):
                n = a.get("name", "") if isinstance(a, dict) else str(a)
                if n:
                    t_artists.append(n)

            t_album = ""
            album_obj = track_data.get("album")
            if isinstance(album_obj, dict):
                t_album = album_obj.get("name", "")

            t_id = (
                track_data.get("uid", "")
                or track_data.get("id", "")
                or track_data.get("uri", "").split(":")[-1]
            )
            t_images = []
            if isinstance(album_obj, dict):
                t_images = album_obj.get("images", [])
            if not t_images:
                cover = track_data.get("coverArt", {}) or {}
                t_images = cover.get("sources", [])
            t_image = t_images[0].get("url", "") if t_images else ""

            meta = TrackMeta(
                name=t_name,
                artists=t_artists if t_artists else ["Unknown"],
                album=t_album,
                duration_ms=int(
                    track_data.get("duration_ms", 0)
                    or track_data.get("duration", 0)
                    or 0
                ),
                spotify_url=f"https://open.spotify.com/track/{t_id}" if t_id else "",
                album_image_url=t_image,
            )
            tracks.append(meta)
    except Exception as e:
        logger.warning("Failed to parse embed playlist", error=str(e))

    return tracks, playlist_name


def _scrape_artist_discography(
    artist_id: str, proxies=None
) -> tuple[list[TrackMeta], str]:
    artist_name = ""
    all_tracks = []

    try:
        resp = requests.get(
            f"https://open.spotify.com/artist/{artist_id}",
            headers=_EMBED_HEADERS,
            proxies=proxies,
            timeout=15,
        )
        if resp.status_code != 200:
            return [], ""

        match = re.search(
            r'<script\s+id="__NEXT_DATA__"\s+type="application/json">\s*({.*?})\s*</script>',
            resp.text,
            re.DOTALL,
        )

        if not match:
            title_match = re.search(r"<title>(.*?)(?:\s*[-|].*)?</title>", resp.text)
            artist_name = title_match.group(1).strip() if title_match else ""

            embed_resp = requests.get(
                f"https://open.spotify.com/embed/artist/{artist_id}",
                headers=_EMBED_HEADERS,
                proxies=proxies,
                timeout=15,
            )
            match = re.search(
                r'<script\s+id="__NEXT_DATA__"\s+type="application/json">\s*({.*?})\s*</script>',
                embed_resp.text,
                re.DOTALL,
            )
            if not match:
                return all_tracks, artist_name

        data = json_module.loads(match.group(1))

        state = _dig(data, "props", "pageProps", "state", "data", "entity") or {}
        if not state:
            state = _dig(data, "props", "pageProps") or data

        profile = state.get("profile", {})
        if isinstance(profile, dict):
            artist_name = profile.get("name", "") or state.get("name", "")
        else:
            artist_name = state.get("name", "")

        discography = state.get("discography", {})
        if isinstance(discography, dict):
            for section_key in ["albums", "singles", "compilations", "all"]:
                section = discography.get(section_key, {})
                if not isinstance(section, dict):
                    continue
                items = section.get("items", [])
                for item in items:
                    releases = _dig(item, "releases", "items") or [item]
                    for release in releases:
                        release_id = release.get("id", "")
                        if release_id:
                            album_tracks, _ = _scrape_embed_album(release_id, proxies)
                            all_tracks.extend(album_tracks)

        if not all_tracks:
            top_tracks = state.get("topTracks", {})
            if isinstance(top_tracks, dict):
                for t in top_tracks.get("items", []):
                    track_data = t.get("track", t) if isinstance(t, dict) else t
                    if not isinstance(track_data, dict):
                        continue
                    t_name = track_data.get("name", "")
                    if not t_name:
                        continue
                    t_artists = [
                        a.get("name", "")
                        for a in track_data.get("artists", [])
                        if isinstance(a, dict)
                    ]
                    t_id = (
                        track_data.get("id", "")
                        or track_data.get("uri", "").split(":")[-1]
                    )
                    album_obj = track_data.get("album", {}) or {}
                    meta = TrackMeta(
                        name=t_name,
                        artists=t_artists
                        if t_artists
                        else [artist_name]
                        if artist_name
                        else ["Unknown"],
                        album=album_obj.get("name", "")
                        if isinstance(album_obj, dict)
                        else "",
                        duration_ms=int(track_data.get("duration_ms", 0) or 0),
                        spotify_url=f"https://open.spotify.com/track/{t_id}"
                        if t_id
                        else "",
                    )
                    all_tracks.append(meta)

    except Exception as e:
        logger.warning("Failed to scrape artist page", error=str(e))

    return all_tracks, artist_name


def resolve_spotify_url(url: str, provider: ConfigProvider = None) -> ResolveResult:
    provider = provider or ConfigProvider()
    try:
        return _resolve_spotify_via_api(url, provider)
    except SpotifyRateLimitError:
        raise
    except Exception as e:
        logger.warning(
            "Spotify API failed, falling back to embed scraping", error=str(e)
        )
        return _resolve_spotify_via_embed(url, provider)


def resolve_youtube_url(url: str) -> ResolveResult:
    url = url.replace("music.youtube.com", "youtube.com").replace(
        "youtu.be", "youtube.com"
    )
    result = ResolveResult()

    if "playlist" in url or "&list=" in url:
        ytmusic = YTMusic()
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(url)
        playlist_id = parse_qs(parsed.query).get("list", [None])[0]
        if playlist_id:
            playlist = ytmusic.get_playlist(playlist_id)
            result.playlist_name = playlist.get("title", "")
            result.is_playlist = True
            for t in playlist.get("tracks", []):
                result.tracks.append(
                    {
                        "url": f"https://www.youtube.com/watch?v={t['videoId']}",
                        "name": t.get("title", ""),
                        "artists": [a["name"] for a in t.get("artists", [])],
                        "duration_ms": (t.get("duration_seconds", 0) or 0) * 1000,
                    }
                )
    elif "channel" in url or "/c/" in url:
        ytmusic = YTMusic()
        channel_id = url.rstrip("/").split("/")[-1]
        try:
            channel = ytmusic.get_artist(channel_id)
            result.playlist_name = channel.get("name", "")
            result.is_playlist = True
            for s in channel.get("songs", {}).get("results", []):
                result.tracks.append(
                    {
                        "url": f"https://www.youtube.com/watch?v={s['videoId']}",
                        "name": s.get("title", ""),
                        "artists": [a["name"] for a in s.get("artists", [])],
                        "duration_ms": 0,
                    }
                )
        except Exception as e:
            logger.warning("Failed to get channel songs", error=str(e))
    else:
        result.tracks.append({"url": url, "name": "", "artists": [], "duration_ms": 0})

    return result


def _get_soundcloud_client_id(provider: ConfigProvider) -> str | None:
    if provider.soundcloud_client_id:
        return provider.soundcloud_client_id
    try:
        response = requests.get("https://soundcloud.com/", timeout=10)
        scripts = re.findall(r'<script crossorigin src="(.*?\.js)"', response.text)
        for script_url in scripts:
            if not script_url.startswith("http"):
                script_url = "https://soundcloud.com" + script_url
            script_content = requests.get(script_url, timeout=10).text
            match = re.search(r'"client_id":"([a-zA-Z0-9]+)"', script_content)
            if match:
                return match.group(1)
    except Exception as e:
        logger.error("Failed to extract SoundCloud client_id", error=str(e))
    return None


def resolve_soundcloud_url(url: str, provider: ConfigProvider = None) -> ResolveResult:
    provider = provider or ConfigProvider()
    client_id = _get_soundcloud_client_id(provider)
    if not client_id:
        raise ConnectionError("Could not obtain SoundCloud client_id")

    result = ResolveResult()

    resolve_api = (
        f"https://api-v2.soundcloud.com/resolve?url={url}&client_id={client_id}"
    )
    try:
        resp = requests.get(resolve_api, timeout=15)
        data = resp.json()
    except Exception as e:
        raise ConnectionError(f"SoundCloud resolve failed: {e}")

    kind = data.get("kind", "")

    if kind == "track":
        result.tracks.append(_sc_track_to_dict(data))

    elif kind == "playlist" or data.get("set_type"):
        result.playlist_name = data.get("title", "")
        result.is_playlist = True
        for t in data.get("tracks", []):
            if t.get("title"):
                result.tracks.append(_sc_track_to_dict(t))

    elif kind == "user":
        result.playlist_name = data.get("username", "") + " — All Tracks"
        result.is_playlist = True
        user_id = data["id"]
        tracks_url = f"https://api-v2.soundcloud.com/users/{user_id}/tracks?client_id={client_id}&limit=200"
        try:
            tracks_resp = requests.get(tracks_url, timeout=15)
            tracks_data = tracks_resp.json()
            for t in tracks_data.get("collection", []):
                result.tracks.append(_sc_track_to_dict(t))
        except Exception as e:
            logger.error("Failed to fetch SC user tracks", error=str(e))

    result._sc_client_id = client_id
    return result


def _sc_track_to_dict(track: dict) -> dict:
    user = track.get("user", {})
    artwork = track.get("artwork_url", "") or ""
    if artwork:
        artwork = artwork.replace("-large", "-t500x500")
    return {
        "sc_id": track.get("id"),
        "name": track.get("title", ""),
        "artists": [user.get("username", "Unknown")],
        "duration_ms": track.get("duration", 0),
        "artwork_url": artwork,
        "permalink_url": track.get("permalink_url", ""),
    }


def download_soundcloud_track(
    permalink_url: str, output_dir: str, client_id: str
) -> str | None:
    cmd = [
        "scdl",
        "-l",
        permalink_url,
        "--path",
        output_dir,
        "--client-id",
        client_id,
        "--onlymp3",
        "-c",
        "--no-playlist-folder",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.error("scdl failed", url=permalink_url, error=str(e))
        return None

    for f in os.listdir(output_dir):
        if f.endswith(".mp3"):
            return os.path.join(output_dir, f)
    return None


def search_youtube_music(
    track_name: str, artist: str, duration_ms: int = 0
) -> str | None:
    ytmusic = YTMusic()
    query = f"{artist} {track_name}"
    results = ytmusic.search(query, filter="songs", limit=5)

    if not results:
        results = ytmusic.search(query, filter="videos", limit=5)
    if not results:
        return None

    if duration_ms > 0:
        target_sec = duration_ms / 1000
        for r in results:
            r_dur = r.get("duration_seconds") or 0
            if r_dur == 0:
                dur_str = r.get("duration", "")
                if dur_str:
                    parts = dur_str.split(":")
                    try:
                        if len(parts) == 2:
                            r_dur = int(parts[0]) * 60 + int(parts[1])
                        elif len(parts) == 3:
                            r_dur = (
                                int(parts[0]) * 3600
                                + int(parts[1]) * 60
                                + int(parts[2])
                            )
                    except ValueError:
                        r_dur = 0
            if abs(r_dur - target_sec) < 5:
                return f"https://www.youtube.com/watch?v={r['videoId']}"

    return f"https://www.youtube.com/watch?v={results[0]['videoId']}"


def download_audio(
    url: str, output_path: str, provider: ConfigProvider = None
) -> str | None:
    provider = provider or ConfigProvider()
    cookie_file = provider.get_youtube_cookie_file()

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",
            },
            {"key": "FFmpegMetadata", "add_metadata": True},
        ],
        "outtmpl": output_path,
        "noplaylist": True,
        "retries": 10,
        "sleep_interval": 1,
        "max_sleep_interval": 5,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
    }

    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

    if provider.proxy_url:
        ydl_opts["proxy"] = provider.proxy_url

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                final = ydl.prepare_filename(info)
                mp3_path = os.path.splitext(final)[0] + ".mp3"
                if os.path.exists(mp3_path):
                    return mp3_path
        return None
    finally:
        if cookie_file and os.path.exists(cookie_file):
            os.unlink(cookie_file)


def detect_source(url: str) -> str:
    url_lower = url.lower()
    if "spotify.com" in url_lower:
        return DownloadJob.Source.SPOTIFY
    if (
        "youtube.com" in url_lower
        or "youtu.be" in url_lower
        or "music.youtube" in url_lower
    ):
        return DownloadJob.Source.YOUTUBE
    if "music.yandex" in url_lower:
        return DownloadJob.Source.YANDEX
    if "soundcloud.com" in url_lower:
        return DownloadJob.Source.SOUNDCLOUD
    return DownloadJob.Source.UNKNOWN


def send_ws_update(data: dict):
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "download_progress",
            {"type": "download.update", "data": data},
        )
    except Exception as e:
        logger.debug("WS send failed", error=str(e))


def send_job_update(job: DownloadJob, extra: dict = None):
    data = {
        "type": "job_update",
        "job_id": job.id,
        "status": job.status,
        "total_tracks": job.total_tracks,
        "processed_tracks": job.processed_tracks,
        "error": job.error,
        "url": job.url,
        "source": job.source,
        "playlist_name": job.playlist_name,
    }
    if extra:
        data.update(extra)
    send_ws_update(data)


def send_track_update(track: DownloadTrack, extra: dict = None):
    data = {
        "type": "track_update",
        "track_id": track.id,
        "job_id": track.job_id,
        "name": track.name,
        "artist_name": track.artist_name,
        "status": track.status,
        "error": track.error,
        "youtube_url": track.youtube_url,
    }
    if extra:
        data.update(extra)
    send_ws_update(data)
