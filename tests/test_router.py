import pytest
from fastapi.testclient import TestClient

from src.acestream_proxy import cache
from src.acestream_proxy.main import app
from src.acestream_proxy.models import Channel, Playlist

client = TestClient(app)


@pytest.fixture
def demo_playlist() -> Playlist:
    return Playlist(
        channels=[
            Channel(name="One", url="acestream://hash1"),
            Channel(name="Two", url="http://host/ace/getstream?id=hash2"),
        ],
        header_attrs='url-tvg="http://epg"',
    )


def _seed(playlist: Playlist) -> str:
    text = playlist.to_m3u()
    cache.store("demo", playlist, text)
    return text


def test_root_endpoint() -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "AceStream Proxy" in data["message"]


def test_get_m3u_ok(demo_playlist: Playlist) -> None:
    text = _seed(demo_playlist)

    response = client.get("/demo.m3u")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.text == text
    assert "etag" in response.headers
    assert response.headers["cache-control"] == "no-cache"


def test_get_m3u_not_modified(demo_playlist: Playlist) -> None:
    _seed(demo_playlist)
    etag = client.get("/demo.m3u").headers["etag"]

    response = client.get("/demo.m3u", headers={"If-None-Match": etag})

    assert response.status_code == 304
    assert response.headers["etag"] == etag


def test_get_m3u_unknown_name_returns_404() -> None:
    response = client.get("/does-not-exist.m3u")
    assert response.status_code == 404


def test_hashes_endpoint(demo_playlist: Playlist) -> None:
    _seed(demo_playlist)

    response = client.get("/demo/hashes")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "demo"
    assert data["count"] == 2
    assert set(data["hashes"]) == {"hash1", "hash2"}


def test_hashes_unknown_name_returns_404() -> None:
    response = client.get("/does-not-exist/hashes")
    assert response.status_code == 404
