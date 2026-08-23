import os

class Settings:
    def __init__(self):
        self.playlist_url = os.environ.get('PLAYLIST_URL')
        self.acestream_server_url = os.environ.get('ACESTREAM_SERVER_URL')
        self.server_port: int = int(os.environ.get('SERVER_PORT', '8000'))
        self.reload_interval: int = int(os.environ.get('RELOAD_INTERVAL', '3600'))
        self.startup_retries: int = int(os.environ.get('STARTUP_RETRIES', '6'))
        self.startup_retry_delay: int = int(os.environ.get('STARTUP_RETRY_DELAY', '5'))

settings = Settings()
