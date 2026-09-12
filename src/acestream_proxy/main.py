import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime

import httpx
from fastapi import FastAPI

from . import cache
from .config import settings
from .models import Playlist
from .router import router
from .service import PlaylistService

logger = logging.getLogger(__name__)

if not logging.root.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def _is_retryable(exc: Exception) -> bool:
    """Return True for transient network / server errors worth retrying."""
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return False


async def _fetch_with_retry(name: str, url: str) -> Playlist | None:
    total_attempts = 1 + settings.startup_retries

    for attempt in range(1, total_attempts + 1):
        try:
            return await PlaylistService.process_playlist(name, url)
        except Exception as exc:
            if not _is_retryable(exc) or attempt == total_attempts:
                logger.error("[%s] Failed to fetch/cache: %s", name, exc)
                return None
            delay = settings.startup_retry_delay * (2 ** (attempt - 1))
            logger.warning(
                "[%s] Attempt %d/%d failed: %s. Retrying in %ds",
                name,
                attempt,
                total_attempts,
                exc,
                delay,
            )
            await asyncio.sleep(delay)

    return None


async def _fetch_one(name: str, url: str) -> None:
    playlist = await _fetch_with_retry(name, url)
    if playlist is not None:
        cache.store(name, playlist, playlist.to_m3u())


async def _fetch_and_cache() -> None:
    await asyncio.gather(
        *[_fetch_one(name, url) for name, url in settings.playlists.items()]
    )


async def _periodic_refresh() -> None:
    while True:
        await asyncio.sleep(settings.reload_interval)
        logger.info("Periodic refresh triggered")
        await _fetch_and_cache()


def _log_task_exception(task: asyncio.Task[None]) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.error("Startup fetch task failed: %s", exc, exc_info=exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings.validate_runtime()
    logger.info("Starting AceStream Proxy on port %s", settings.server_port)
    logger.info("Reload interval: %ss", settings.reload_interval)

    if not settings.playlists:
        logger.warning(
            "No playlists configured. Set PLAYLIST_URLS=name:url;name2:url2"
        )
    else:
        logger.info("Configured playlists (%d):", len(settings.playlists))
        for name in settings.playlists:
            logger.info(
                "  http://localhost:%s/%s.m3u", settings.server_port, name
            )

    startup_task = asyncio.create_task(_fetch_and_cache())
    startup_task.add_done_callback(_log_task_exception)
    refresh_task = asyncio.create_task(_periodic_refresh())

    yield

    logger.info("Shutting down AceStream Proxy")
    startup_task.cancel()
    refresh_task.cancel()
    for task in (startup_task, refresh_task):
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="AceStream M3U Proxy",
    description="Proxy for modifying M3U playlists to point to local AceStream server",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/")
async def root() -> dict[str, object]:
    playlists: dict[str, object] = {}
    for name in settings.playlists:
        timestamp = cache.get_last_fetched(name)
        playlists[f"/{name}.m3u"] = {
            "description": f"Playlist '{name}'",
            "last_updated": (
                datetime.fromtimestamp(timestamp).isoformat()
                if timestamp is not None
                else None
            ),
        }
    return {"message": "AceStream Proxy API", "playlists": playlists}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.acestream_proxy.main:app",
        host="0.0.0.0",  # noqa: S104
        port=settings.server_port,
    )
