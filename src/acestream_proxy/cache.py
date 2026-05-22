import logging
import time

from .models import Playlist

logger = logging.getLogger(__name__)

_cached_playlist: Playlist | None = None
_cached_playlist_text: str | None = None
_last_fetched: float = 0


def get_cached_playlist() -> Playlist | None:
    return _cached_playlist


def get_cached_playlist_text() -> str | None:
    return _cached_playlist_text


def get_last_fetched() -> float:
    return _last_fetched


def store(playlist: Playlist, playlist_text: str) -> None:
    global _cached_playlist, _cached_playlist_text, _last_fetched
    _cached_playlist = playlist
    _cached_playlist_text = playlist_text
    _last_fetched = time.time()
    logger.info(f"Playlist cached at {time.ctime(_last_fetched)} ({len(playlist.channels)} channels)")
