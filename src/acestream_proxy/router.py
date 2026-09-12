from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from . import cache
from .models import Playlist

router = APIRouter()


@router.get("/{name}.m3u", response_class=PlainTextResponse)
async def get_playlist_m3u(name: str) -> PlainTextResponse:
    text = cache.get_cached_playlist_text(name)
    if text is None:
        raise HTTPException(status_code=404, detail=f"Playlist '{name}' not found or not yet available")
    return PlainTextResponse(content=text, media_type="text/html")


@router.get("/{name}/hashes")
async def get_hashes(name: str) -> dict:
    playlist = cache.get_cached_playlist(name)
    if playlist is None:
        raise HTTPException(status_code=404, detail=f"Playlist '{name}' not found or not yet available")
    hashes = playlist.get_acestream_hashes()
    return {"name": name, "hashes": hashes, "count": len(hashes)}
