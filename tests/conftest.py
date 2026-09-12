import os

# Must run before any application module is imported so pydantic-settings
# picks these up at import time.
os.environ.setdefault(
    "ACESTREAM_SERVER_URL",
    "http://localhost:6878/acestream/video?id={hash}",
)
os.environ.setdefault("PLAYLIST_URLS", "")
