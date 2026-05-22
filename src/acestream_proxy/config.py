import os

class Settings:
    def __init__(self):
        self.playlist_url = os.environ.get('PLAYLIST_URL')
        self.acestream_server_url = os.environ.get('ACESTREAM_SERVER_URL')
        self.server_port: int = int(os.environ.get('SERVER_PORT', '8000'))
        self.reload_interval: int = int(os.environ.get('RELOAD_INTERVAL', '3600'))

settings = Settings()
