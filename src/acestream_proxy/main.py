import asyncio
import logging
from contextlib import asynccontextmanager

from httpx import ConnectError

from fastapi import FastAPI

from . import cache
from .config import settings
from .router import router
from .service import PlaylistService

logger = logging.getLogger(__name__)

if not logging.root.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def _playlist_to_text(playlist) -> str:
    header = "#EXTM3U"
    if playlist.header_attrs:
        header += f" {playlist.header_attrs}"
    lines = [header]
    if playlist.extgrp_lines:
        lines.extend(playlist.extgrp_lines)
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
    return "\n".join(lines)


async def _fetch_one(name: str, url: str) -> None:
    try:
        playlist = await PlaylistService.process_playlist(name, url)
    except ConnectError as e:
        logger.warning(f"[{name}] Connection error: {e}. Retrying...")
        for attempt in range(1, settings.startup_retries + 1):
            delay = settings.startup_retry_delay * (2 ** (attempt - 1))
            logger.info(f"[{name}] Retry {attempt}/{settings.startup_retries} in {delay}s")
            await asyncio.sleep(delay)
            try:
                playlist = await PlaylistService.process_playlist(name, url)
                break
            except ConnectError as retry_err:
                logger.warning(f"[{name}] Retry {attempt} failed: {retry_err}")
        else:
            logger.error(f"[{name}] Failed after {settings.startup_retries} retries")
            return
    except Exception as e:
        logger.error(f"[{name}] Failed to fetch/cache: {e}")
        return

    cache.store(name, playlist, _playlist_to_text(playlist))


async def _fetch_and_cache() -> None:
    await asyncio.gather(*[_fetch_one(name, url) for name, url in settings.playlists.items()])


async def _periodic_refresh() -> None:
    while True:
        await asyncio.sleep(settings.reload_interval)
        logger.info("Periodic refresh triggered")
        await _fetch_and_cache()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting AceStream Proxy on port {settings.server_port}")
    logger.info(f"Reload interval: {settings.reload_interval}s")
    if not settings.playlists:
        logger.warning("No playlists configured. Set PLAYLIST_URLS=name:url;name2:url2")
    else:
        logger.info(f"Configured playlists ({len(settings.playlists)}):")
        for name in settings.playlists:
            logger.info(f"  http://localhost:{settings.server_port}/{name}.m3u")

    asyncio.create_task(_fetch_and_cache())
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

app.include_router(router)


@app.get("/")
async def root() -> dict:
    return {
        "message": "AceStream Proxy API",
        "playlists": {f"/{name}.m3u": f"Playlist '{name}'" for name in settings.playlists},
    }
