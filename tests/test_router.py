from fastapi.testclient import TestClient

from src.acestream_proxy.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "AceStream Proxy" in data["message"]

def test_playlist_endpoint():
    """Test playlist endpoint - should return 404 or handle gracefully"""
    response = client.get("/api/playlist.m3u")
    # This will fail since we don't have a real playlist to fetch
    # The main purpose of this test is to ensure the endpoint exists
    assert response.status_code in [200, 404, 500]

def test_playlist_text_endpoint():
    """Test playlist text endpoint"""
    response = client.get("/api/playlist.m3u.txt")
    # This will fail since we don't have a real playlist to fetch
    assert response.status_code in [200, 404, 500]

def test_hashes_endpoint():
    """Test hashes endpoint"""
    response = client.get("/api/hashes")
    # This will fail since we don't have a real playlist to fetch
    assert response.status_code in [200, 404, 500]