import pytest

from src.acestream_proxy.config import Settings


def test_parse_playlists_multi() -> None:
    parsed = Settings._parse_playlists("a:http://x;b:http://y")
    assert parsed == {"a": "http://x", "b": "http://y"}


def test_parse_playlists_ignores_invalid_entries() -> None:
    parsed = Settings._parse_playlists("bad; :x; a:;  b:http://y  ")
    assert parsed == {"b": "http://y"}


def test_playlists_prefers_multi_over_legacy() -> None:
    settings = Settings(playlist_urls="a:http://x", playlist_url="http://legacy")
    assert settings.playlists == {"a": "http://x"}


def test_playlists_legacy_fallback() -> None:
    settings = Settings(playlist_urls="", playlist_url="http://legacy/list.m3u")
    assert settings.playlists == {"hashes": "http://legacy/list.m3u"}


def test_validate_runtime_missing_url() -> None:
    settings = Settings(acestream_server_url=None)
    with pytest.raises(ValueError, match="ACESTREAM_SERVER_URL"):
        settings.validate_runtime()


def test_validate_runtime_missing_placeholder() -> None:
    settings = Settings(acestream_server_url="http://srv/stream")
    with pytest.raises(ValueError, match="ACESTREAM_SERVER_URL"):
        settings.validate_runtime()


def test_validate_runtime_ok() -> None:
    settings = Settings(acestream_server_url="http://srv/acestream/video?id={hash}")
    settings.validate_runtime()
