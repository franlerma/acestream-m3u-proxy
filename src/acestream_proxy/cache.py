import logging
import time

from .models import Playlist

logger = logging.getLogger(__name__)

_cached_playlists: dict[str, Playlist] = {}
_cached_playlists_text: dict[str, str] = {}
_last_fetched: dict[str, float] = {}


def get_cached_playlist(name: str) -> Playlist | None:
    return _cached_playlists.get(name)


def get_cached_playlist_text(name: str) -> str | None:
    return _cached_playlists_text.get(name)


def get_last_fetched(name: str) -> float | None:
    return _last_fetched.get(name)


def get_available_names() -> list[str]:
    return list(_cached_playlists)


def store(name: str, playlist: Playlist, playlist_text: str) -> None:
    _cached_playlists[name] = playlist
    _cached_playlists_text[name] = playlist_text
    _last_fetched[name] = time.time()
    logger.info("Playlist '%s' cached: %d channels", name, len(playlist.channels))
