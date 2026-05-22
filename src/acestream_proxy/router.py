from fastapi import APIRouter, HTTPException

from . import cache
from .models import Playlist

router = APIRouter()


def _get_playlist_or_raise() -> Playlist:
    playlist = cache.get_cached_playlist()
    if playlist is None:
        raise HTTPException(status_code=503, detail="Playlist not yet available, try again shortly")
    return playlist


@router.get("/playlist.m3u", response_model=Playlist)
async def get_playlist_endpoint() -> Playlist:
    return _get_playlist_or_raise()


@router.get("/playlist.m3u.txt")
async def get_playlist_text() -> str:
    text = cache.get_cached_playlist_text()
    if text is None:
        raise HTTPException(status_code=503, detail="Playlist not yet available, try again shortly")
    return text


@router.get("/hashes")
async def get_hashes() -> dict:
    playlist = _get_playlist_or_raise()
    hashes = playlist.get_acestream_hashes()
    return {"hashes": hashes, "count": len(hashes)}
