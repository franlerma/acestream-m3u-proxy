from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, Field


class Channel(BaseModel):
    """Represents a channel in the M3U playlist."""

    name: str
    url: str
    group_title: str | None = None
    tvg_id: str | None = None
    tvg_logo: str | None = None
    raw_extinf: str | None = None
    leading_lines: list[str] = Field(default_factory=list)
    extra_lines: list[str] = Field(default_factory=list)


class Playlist(BaseModel):
    """Represents a complete playlist."""

    channels: list[Channel]
    header_attrs: str = ""  # raw attributes from #EXTM3U line
    leading_lines: list[str] = Field(default_factory=list)

    def get_acestream_hashes(self) -> list[str]:
        """Extract all acestream hashes from the playlist."""
        hashes: set[str] = set()
        for channel in self.channels:
            hash_value = extract_acestream_hash(channel.url)
            if hash_value:
                hashes.add(hash_value)
        return list(hashes)

    def to_m3u(self) -> str:
        """Serialize the playlist back to M3U text."""
        header = "#EXTM3U"
        if self.header_attrs:
            header += f" {self.header_attrs}"
        lines: list[str] = [header]
        lines.extend(self.leading_lines)

        for channel in self.channels:
            lines.extend(channel.leading_lines)
            lines.append(channel.raw_extinf or _build_extinf(channel))
            lines.extend(channel.extra_lines)
            lines.append(channel.url)

        return "\n".join(lines)


def _build_extinf(channel: Channel) -> str:
    """Reconstruct an #EXTINF line when the raw one is unavailable."""
    extinf = "#EXTINF:-1"
    if channel.group_title:
        extinf += f' group-title="{channel.group_title}"'
    if channel.tvg_id:
        extinf += f' tvg-id="{channel.tvg_id}"'
    if channel.tvg_logo:
        extinf += f' tvg-logo="{channel.tvg_logo}"'
    extinf += f",{channel.name or 'Unknown'}"
    return extinf


def is_acestream_url(url: str) -> bool:
    """Check if URL is an AceStream URL."""
    return extract_acestream_hash(url) is not None


def extract_acestream_hash(url: str) -> str | None:
    """Extract the hash from an AceStream URL.

    Supports both ``acestream://<hash>`` and
    ``http://.../ace/getstream?id=<hash>`` formats.
    """
    if not url:
        return None

    if url.startswith("acestream://"):
        acestream_hash: str | None = (
            url[len("acestream://") :].split("?", 1)[0].strip("/") or None
        )
        return acestream_hash

    parsed = urlparse(url)
    if "ace/getstream" in parsed.path:
        query_hash: str | None = parse_qs(parsed.query).get("id", [None])[0]
        return query_hash or None

    return None
