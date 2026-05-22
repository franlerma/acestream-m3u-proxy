import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from . import cache
from .config import settings
from .router import router
from .service import PlaylistService

logger = logging.getLogger(__name__)

# Configure logging so logger outputs are visible
if not logging.root.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

async def _fetch_and_cache() -> None:
    """Fetch playlist, process it, and store in cache."""
    try:
        playlist = await PlaylistService.process_playlist()
    except Exception as e:
        logger.error(f"Failed to fetch/cache playlist: {e}")
        return

    lines = ["#EXTM3U"]
    for ch in playlist.channels:
        extinf = "#EXTINF:-1"
        if ch.group_title:
            extinf += f' group-title="{ch.group_title}"'
        if ch.tvg_id:
            extinf += f' tvg-id="{ch.tvg_id}"'
        if ch.tvg_logo:
            extinf += f' tvg-logo="{ch.tvg_logo}"'
        extinf += f",{ch.name or 'Unknown'}"
        lines.append(extinf)
        lines.append(ch.url)
    logger.info(f"Cached {len(playlist.channels)} channels")
    cache.store(playlist, "\n".join(lines))


async def _periodic_refresh() -> None:
    """Background task: refresh cache every reload_interval seconds."""
    while True:
        await asyncio.sleep(settings.reload_interval)
        logger.info("Periodic refresh triggered")
        await _fetch_and_cache()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting AceStream Proxy on port {settings.server_port}")
    logger.info(f"Playlist URL: {settings.playlist_url}")
    logger.info(f"Reload interval: {settings.reload_interval}s")

    # Launch initial fetch as background task so uvicorn starts immediately
    asyncio.create_task(_fetch_and_cache())
    # Launch periodic refresh
    refresh_task = asyncio.create_task(_periodic_refresh())

    yield

    logger.info("Shutting down AceStream Proxy")
    refresh_task.cancel()
    try:
        await refresh_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="AceStream M3U Proxy",
    description="Proxy for modifying M3U playlists to point to local AceStream server",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root() -> dict:
    return {
        "message": "AceStream Proxy API",
        "endpoints": {
            "GET /api/playlist.m3u": "Processed playlist as JSON",
            "GET /api/playlist.m3u.txt": "Processed playlist as plain M3U text",
            "GET /api/hashes": "All AceStream hashes",
            "GET /hashes.m3u": "Alias for /api/playlist.m3u.txt",
        },
    }


@app.get("/hashes.m3u", response_class=PlainTextResponse)
async def get_hashes_m3u() -> PlainTextResponse:
    text = cache.get_cached_playlist_text() or ""
    return PlainTextResponse(content=text, media_type="audio/x-mpegurl")
