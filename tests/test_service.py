from src.acestream_proxy.models import (
    Channel,
    Playlist,
    extract_acestream_hash,
    is_acestream_url,
    replace_hash_in_url,
)


def test_is_acestream_url():
    """Test AceStream URL detection"""
    assert is_acestream_url("acestream://abc123") == True
    assert is_acestream_url("http://example.com") == False
    assert is_acestream_url("") == False

def test_extract_acestream_hash():
    """Test extracting hash from AceStream URL"""
    assert extract_acestream_hash("acestream://abc123") == "abc123"
    assert extract_acestream_hash("acestream://") == ""
    assert extract_acestream_hash("http://example.com") is None

def test_replace_hash_in_url():
    """Test replacing hash in URL"""
    base_url = "http://localhost:6878/{hash}"
    hash_value = "abc123"
    expected = "http://localhost:6878/abc123"
    assert replace_hash_in_url(base_url, hash_value) == expected

def test_channel_model():
    """Test Channel model"""
    channel = Channel(
        name="Test Channel",
        url="acestream://abc123"
    )
    
    assert channel.name == "Test Channel"
    assert channel.url == "acestream://abc123"

def test_playlist_model():
    """Test Playlist model"""
    channel1 = Channel(
        name="Channel 1",
        url="acestream://abc123"
    )
    channel2 = Channel(
        name="Channel 2", 
        url="http://example.com"
    )
    
    playlist = Playlist(channels=[channel1, channel2])
    
    assert len(playlist.channels) == 2
    assert len(playlist.get_hashed_channels()) == 1
    assert len(playlist.get_acestream_hashes()) == 1