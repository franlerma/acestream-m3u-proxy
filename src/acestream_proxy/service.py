import logging
import re

from httpx import AsyncClient

from .config import settings
from .models import Channel, Playlist, extract_acestream_hash

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class PlaylistService:
    """Fetch, parse and rewrite M3U playlists."""

    @staticmethod
    async def fetch_playlist(url: str) -> str:
        headers = {"User-Agent": _USER_AGENT}
        async with AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            logger.info(
                "Fetched playlist from %s: %d chars, first 500: %r",
                url,
                len(response.text),
                response.text[:500],
            )
            return response.text

    @staticmethod
    def parse_m3u(content: str) -> Playlist:
        lines = content.strip().split("\n")
        channels: list[Channel] = []
        current_channel: Channel | None = None
        pending_leading: list[str] = []
        header_attrs: str = ""

        for raw_line in lines:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#EXTM3U"):
                header_attrs = line[len("#EXTM3U") :].strip()
                continue

            if line.startswith("#EXTINF:"):
                current_channel = Channel(
                    name="",
                    url="",
                    raw_extinf=line,
                    leading_lines=list(pending_leading),
                )
                pending_leading = []

                name_match = re.search(r'(?:^|\s)title="([^"]*)"', line)
                if name_match:
                    current_channel.name = name_match.group(1)
                else:
                    parts = line.split(",", 1)
                    if len(parts) > 1:
                        current_channel.name = parts[1].strip()

                group_match = re.search(r'group-title="([^"]*)"', line)
                if group_match:
                    current_channel.group_title = group_match.group(1)

                tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
                if tvg_id_match:
                    current_channel.tvg_id = tvg_id_match.group(1)

                tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', line)
                if tvg_logo_match:
                    current_channel.tvg_logo = tvg_logo_match.group(1)
                continue

            if line.startswith("#"):
                if current_channel is not None:
                    current_channel.extra_lines.append(line)
                else:
                    pending_leading.append(line)
                continue

            if current_channel is not None:
                current_channel.url = line
                channels.append(current_channel)
                current_channel = None

        if channels and pending_leading:
            channels[-1].extra_lines.extend(pending_leading)

        leading_lines = pending_leading if not channels else []
        return Playlist(
            channels=channels,
            header_attrs=header_attrs,
            leading_lines=leading_lines,
        )

    @staticmethod
    def generate_modified_playlist(original_playlist: Playlist) -> Playlist:
        base_url = settings.acestream_server_url or ""
        modified_channels: list[Channel] = []

        for channel in original_playlist.channels:
            hash_value = extract_acestream_hash(channel.url)
            if hash_value:
                modified_url = base_url.replace("{hash}", hash_value)
                modified_channels.append(
                    channel.model_copy(update={"url": modified_url})
                )
            else:
                modified_channels.append(channel)

        return Playlist(
            channels=modified_channels,
            header_attrs=original_playlist.header_attrs,
            leading_lines=original_playlist.leading_lines,
        )

    @staticmethod
    async def process_playlist(name: str, url: str) -> Playlist:
        content = await PlaylistService.fetch_playlist(url)
        playlist = PlaylistService.parse_m3u(content)
        logger.info("Loaded %d channels from '%s'", len(playlist.channels), name)
        return PlaylistService.generate_modified_playlist(playlist)
