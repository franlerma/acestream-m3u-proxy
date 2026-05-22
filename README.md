# AceStream M3U Proxy

A web service that fetches M3U playlists containing AceStream channels and rewrites their URLs to point to a local AceStream server.

## Features

- Fetches and parses M3U playlists from remote URLs (including IPFS/IPNS gateways)
- Identifies AceStream channels in both `acestream://` and `http://.../ace/getstream?id=` formats
- Replaces AceStream URLs with a configurable local server URL
- Serves the modified playlist via HTTP with correct `audio/x-mpegurl` content type
- Periodic background cache refresh

## Endpoints

- `GET /` - API info
- `GET /hashes.m3u` - Modified playlist as M3U text (`audio/x-mpegurl`)
- `GET /api/playlist.m3u` - Modified playlist as JSON
- `GET /api/playlist.m3u.txt` - Modified playlist as plain text
- `GET /api/hashes` - All AceStream hashes extracted from the playlist

## Quick Start with Docker

1. Copy `.env.example` to `.env` and adjust the values:
   ```
   PLAYLIST_URL=https://ipfs.io/ipns/<cid>/hashes.m3u
   ACESTREAM_SERVER_URL=http://<acestream-host>:<port>/acestream/video?id={hash}
   SERVER_PORT=8000
   RELOAD_INTERVAL=3600
   ```

2. Run with Docker Compose:
   ```bash
   docker compose up -d
   ```

3. Use the playlist at `http://localhost:8000/hashes.m3u`

## License

MIT
