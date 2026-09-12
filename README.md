# AceStream M3U Proxy

A web service that fetches M3U playlists containing AceStream channels and rewrites their URLs to point to a local AceStream server.

## Features

- Fetches and parses M3U playlists from remote URLs (including IPFS/IPNS gateways)
- Identifies AceStream channels in both `acestream://<hash>` and `http://.../ace/getstream?id=<hash>` formats
- Preserves M3U fidelity: raw `#EXTINF` lines, leading comments, `#EXTGRP`/`#EXTVLCOPT` lines and the `#EXTM3U` header attributes
- Rewrites AceStream URLs to a configurable local server URL
- Serves the modified playlist as `text/html` with `ETag` + `304 Not Modified` support
- Per-playlist cache with `last_updated` timestamps
- Startup retries with exponential backoff for transient network / 5xx errors
- Periodic background cache refresh

## Endpoints

- `GET /` — API info, including each configured playlist and its `last_updated` timestamp
- `GET /{name}.m3u` — modified playlist as M3U text (`text/html`), with `ETag` and `Cache-Control: no-cache`
- `GET /{name}/hashes` — JSON list of AceStream hashes for a playlist

## Configuration

Copy `.env.example` to `.env` and adjust the values.

| Variable | Default | Description |
|----------|---------|-------------|
| `PLAYLIST_URLS` | *(empty)* | Semicolon-separated `name:url` entries, e.g. `elCano:http://host/a.m3u;newEra:http://host/b.m3u` |
| `PLAYLIST_URL` | *(empty)* | Legacy single-playlist setting; used as `hashes:<url>` when `PLAYLIST_URLS` is empty |
| `ACESTREAM_SERVER_URL` | *(none)* | Target URL for rewritten channels. **Must contain the `{hash}` placeholder**, e.g. `http://192.168.2.10:15123/acestream/video?id={hash}` |
| `SERVER_PORT` | `8000` | Port the service listens on |
| `RELOAD_INTERVAL` | `3600` | Seconds between background cache refreshes |
| `STARTUP_RETRIES` | `6` | Number of retries after the initial fetch fails |
| `STARTUP_RETRY_DELAY` | `5` | Base delay in seconds for exponential backoff (`delay * 2**(attempt-1)`) |

Startup aborts with a clear error if `ACESTREAM_SERVER_URL` is missing or lacks `{hash}`.

## Quick Start with Docker

1. Copy `.env.example` to `.env` and adjust the values.
2. Run with Docker Compose:
   ```bash
   make up        # docker compose up --build -d
   ```
3. Use the playlist at `http://localhost:<SERVER_PORT>/<name>.m3u`.

## Development

```bash
make install   # uv sync --extra dev
make test      # uv run pytest
make lint      # ruff check + format
make typecheck # mypy src/
make run       # uv run python -m src.acestream_proxy.main
```

`uv.lock` is committed; `uv` is the source of truth for dependencies.

## License

MIT
