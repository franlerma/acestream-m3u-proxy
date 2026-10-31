import hashlib

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response

from . import cache

router = APIRouter()


@router.get("/{name}.m3u")
async def get_playlist_m3u(
    name: str,
    if_none_match: str | None = Header(default=None),
) -> Response:
    text = cache.get_cached_playlist_text(name)
    if text is None:
        raise HTTPException(
            status_code=404,
            detail=f"Playlist '{name}' not found or not yet available",
        )

    etag = '"' + hashlib.sha1(text.encode(), usedforsecurity=False).hexdigest() + '"'
    headers = {"ETag": etag, "Cache-Control": "no-cache"}

    if if_none_match == etag:
        return Response(status_code=304, headers=headers)

    return Response(content=text, media_type="text/plain", headers=headers)


@router.get("/{name}/hashes")
async def get_hashes(name: str) -> dict[str, object]:
    playlist = cache.get_cached_playlist(name)
    if playlist is None:
        raise HTTPException(
            status_code=404,
            detail=f"Playlist '{name}' not found or not yet available",
        )
    hashes = playlist.get_acestream_hashes()
    return {"name": name, "hashes": hashes, "count": len(hashes)}
