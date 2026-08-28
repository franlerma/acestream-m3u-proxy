import logging
import time

from .models import Playlist

logger = logging.getLogger(__name__)

_cached_playlists: dict[str, Playlist] = {}
_cached_playlists_text: dict[str, str] = {}
_last_fetched: float = 0


def get_cached_playlist(name: str) -> Playlist | None:
    return _cached_playlists.get(name)


def get_cached_playlist_text(name: str) -> str | None:
    return _cached_playlists_text.get(name)


def get_last_fetched() -> float:
    return _last_fetched


def get_available_names() -> list[str]:
    return list(_cached_playlists.keys())


def store(name: str, playlist: Playlist, playlist_text: str) -> None:
    global _last_fetched
    _cached_playlists[name] = playlist
    _cached_playlists_text[name] = playlist_text
    _last_fetched = time.time()
    logger.info(f"Playlist '{name}' cached: {len(playlist.channels)} channels")
