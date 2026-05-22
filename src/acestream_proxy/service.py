import logging
import re

from httpx import AsyncClient

from .config import settings
from .models import Channel, Playlist

logger = logging.getLogger(__name__)


class PlaylistService:
    """Service for processing M3U playlists"""

    @staticmethod
    async def fetch_playlist(url: str) -> str:
        """Fetch playlist content from URL"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            logger.info(f"Fetched playlist from {url}: {len(response.text)} chars, first 500: {response.text[:500]!r}")
            return response.text

    @staticmethod
    def parse_m3u(content: str) -> Playlist:
        """Parse M3U content into a Playlist object"""
        lines = content.strip().split('\n')
        channels: list[Channel] = []
        current_channel: Channel | None = None
        header_attrs: str = ""
        extgrp_lines: list[str] = []

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if line.startswith('#EXTM3U'):
                # Preserve everything after #EXTM3U
                header_attrs = line[len('#EXTM3U'):].strip()
                continue

            if line.startswith('#EXTGRP:'):
                extgrp_lines.append(line)
                continue

            if line.startswith('#EXTINF:'):
                current_channel = Channel(name='', url='')

                # Extract name: prefer after last comma
                name_match = re.search(r'title="([^"]*)"', line)
                if name_match:
                    current_channel.name = name_match.group(1)
                else:
                    parts = line.split(',', 1)
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

            if line.startswith('#'):
                continue

            # URL line
            if current_channel:
                current_channel.url = line
                channels.append(current_channel)
                current_channel = None

        return Playlist(channels=channels, header_attrs=header_attrs, extgrp_lines=extgrp_lines)

    @staticmethod
    def _extract_hash(url: str) -> str | None:
        """Extract acestream hash from acestream:// or /ace/getstream?id= URLs"""
        if url.startswith("acestream://"):
            return url.split("://")[1]
        if "ace/getstream?id=" in url:
            return url.split("id=")[1].split("&")[0]
        return None

    @staticmethod
    def generate_modified_playlist(original_playlist: Playlist) -> Playlist:
        """Generate a new playlist with modified URLs pointing to local AceStream server"""
        modified_channels = []

        for channel in original_playlist.channels:
            hash_value = PlaylistService._extract_hash(channel.url)
            if hash_value:
                modified_url = settings.acestream_server_url.replace("{hash}", hash_value)
                modified_channel = Channel(
                    name=channel.name,
                    url=modified_url,
                    group_title=channel.group_title,
                    tvg_id=channel.tvg_id,
                    tvg_logo=channel.tvg_logo
                )
                modified_channels.append(modified_channel)
            else:
                modified_channels.append(channel)

        return Playlist(
            channels=modified_channels,
            header_attrs=original_playlist.header_attrs,
            extgrp_lines=original_playlist.extgrp_lines,
        )

    @staticmethod
    async def process_playlist() -> Playlist:
        """Fetch, parse, and process the playlist"""
        content = await PlaylistService.fetch_playlist(settings.playlist_url)
        original_playlist = PlaylistService.parse_m3u(content)
        return PlaylistService.generate_modified_playlist(original_playlist)
