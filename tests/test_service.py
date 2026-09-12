import pytest

from src.acestream_proxy import service
from src.acestream_proxy.models import (
    Channel,
    Playlist,
    extract_acestream_hash,
    is_acestream_url,
)

SAMPLE_M3U = """#EXTM3U url-tvg="http://epg.example/xmltv.xml"

# Leading comment
#EXTGRP:News
#EXTINF:-1 tvg-id="id1" group-title="News" tvg-logo="http://logo/1.png",Channel One
#EXTVLCOPT:http-user-agent=CustomAgent
acestream://hash1
#EXTINF:-1,Channel Two
http://example.com/plain.m3u8
"""


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("acestream://abc123", "abc123"),
        ("acestream://abc123?x=1", "abc123"),
        ("acestream://abc123/", "abc123"),
        ("http://host/ace/getstream?id=HASH&foo=bar", "HASH"),
        ("http://host/ace/getstream?id=HASH", "HASH"),
        ("acestream://", None),
        ("acestream://?x=1", None),
        ("http://host/ace/getstream?foo=bar", None),
        ("http://example.com", None),
        ("", None),
    ],
)
def test_extract_acestream_hash(url: str, expected: str | None) -> None:
    assert extract_acestream_hash(url) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("acestream://abc123", True),
        ("http://host/ace/getstream?id=HASH", True),
        ("http://example.com", False),
        ("", False),
    ],
)
def test_is_acestream_url(url: str, expected: bool) -> None:
    assert is_acestream_url(url) is expected


def test_parse_m3u_preserves_fidelity() -> None:
    playlist = service.PlaylistService.parse_m3u(SAMPLE_M3U)

    assert playlist.header_attrs == 'url-tvg="http://epg.example/xmltv.xml"'
    assert len(playlist.channels) == 2

    first = playlist.channels[0]
    assert first.raw_extinf == (
        '#EXTINF:-1 tvg-id="id1" group-title="News" '
        'tvg-logo="http://logo/1.png",Channel One'
    )
    assert first.name == "Channel One"
    assert first.group_title == "News"
    assert first.tvg_id == "id1"
    assert first.tvg_logo == "http://logo/1.png"
    assert first.leading_lines == ["# Leading comment", "#EXTGRP:News"]
    assert first.extra_lines == ["#EXTVLCOPT:http-user-agent=CustomAgent"]
    assert first.url == "acestream://hash1"

    second = playlist.channels[1]
    assert second.raw_extinf == "#EXTINF:-1,Channel Two"
    assert second.leading_lines == []
    assert second.extra_lines == []
    assert second.url == "http://example.com/plain.m3u8"


def test_parse_m3u_only_comments_go_to_playlist_leading() -> None:
    playlist = service.PlaylistService.parse_m3u("#EXTM3U\n# just a comment\n")
    assert playlist.channels == []
    assert playlist.leading_lines == ["# just a comment"]


def test_to_m3u_round_trip() -> None:
    original = service.PlaylistService.parse_m3u(SAMPLE_M3U)
    reparsed = service.PlaylistService.parse_m3u(original.to_m3u())

    assert reparsed.header_attrs == original.header_attrs
    assert len(reparsed.channels) == len(original.channels)

    for before, after in zip(original.channels, reparsed.channels, strict=True):
        assert after.raw_extinf == before.raw_extinf
        assert after.leading_lines == before.leading_lines
        assert after.extra_lines == before.extra_lines
        assert after.url == before.url
        assert after.name == before.name


def test_to_m3u_reconstructs_extinf_when_missing() -> None:
    playlist = Playlist(
        channels=[
            Channel(
                name="News",
                url="acestream://h",
                group_title="G",
                tvg_id="i",
                tvg_logo="l",
            )
        ]
    )
    expected = (
        "#EXTM3U\n"
        '#EXTINF:-1 group-title="G" tvg-id="i" tvg-logo="l",News\n'
        "acestream://h"
    )
    assert playlist.to_m3u() == expected


def test_generate_modified_playlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service.settings,
        "acestream_server_url",
        "http://srv/acestream/video?id={hash}",
    )
    original = Playlist(
        channels=[
            Channel(name="A", url="acestream://h1", raw_extinf="#EXTINF:-1,A"),
            Channel(name="B", url="http://host/ace/getstream?id=h2&foo=bar"),
            Channel(name="C", url="http://example.com/plain.m3u8"),
        ],
        header_attrs='url-tvg="x"',
        leading_lines=["# header note"],
    )

    result = service.PlaylistService.generate_modified_playlist(original)

    assert result.channels[0].url == "http://srv/acestream/video?id=h1"
    assert result.channels[1].url == "http://srv/acestream/video?id=h2"
    assert result.channels[2].url == "http://example.com/plain.m3u8"
    assert result.channels[0].raw_extinf == "#EXTINF:-1,A"
    assert result.channels[2].raw_extinf is None
    assert result.header_attrs == 'url-tvg="x"'
    assert result.leading_lines == ["# header note"]


def test_get_acestream_hashes() -> None:
    playlist = Playlist(
        channels=[
            Channel(name="A", url="acestream://h1"),
            Channel(name="B", url="http://host/ace/getstream?id=h2"),
            Channel(name="C", url="http://example.com/plain.m3u8"),
        ]
    )
    assert set(playlist.get_acestream_hashes()) == {"h1", "h2"}
