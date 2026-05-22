from pydantic import BaseModel


class Channel(BaseModel):
    """Represents a channel in the M3U playlist"""
    name: str
    url: str
    group_title: str | None = None
    tvg_id: str | None = None
    tvg_logo: str | None = None


class Playlist(BaseModel):
    """Represents a complete playlist"""
    channels: list[Channel]
    header_attrs: str = ""       # raw attributes from #EXTM3U line (url-tvg, refresh, etc.)
    extgrp_lines: list[str] = [] # raw #EXTGRP lines to preserve

    def get_hashed_channels(self) -> list[Channel]:
        """Get only channels that have acestream hashes"""
        return [channel for channel in self.channels if is_acestream_url(channel.url)]

    def get_acestream_hashes(self) -> list[str]:
        """Extract all acestream hashes from the playlist"""
        hashes = set()
        for channel in self.channels:
            hash_value = extract_acestream_hash(channel.url)
            if hash_value:
                hashes.add(hash_value)
        return list(hashes)


def is_acestream_url(url: str) -> bool:
    """Check if URL is an AceStream URL"""
    return url.startswith("acestream://")


def extract_acestream_hash(url: str) -> str | None:
    """Extract the hash from an AceStream URL"""
    if not is_acestream_url(url):
        return None
    try:
        return url.split("://")[1]
    except (IndexError, AttributeError):
        return None


def replace_hash_in_url(base_url: str, hash_value: str) -> str:
    """Replace {hash} wildcard in base URL with actual hash"""
    return base_url.replace("{hash}", hash_value)
