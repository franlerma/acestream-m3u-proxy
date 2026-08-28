import os


class Settings:
    def __init__(self):
        raw = os.environ.get('PLAYLIST_URLS', '')
        if not raw:
            legacy = os.environ.get('PLAYLIST_URL', '')
            if legacy:
                raw = f'hashes:{legacy}'
        self.playlists: dict[str, str] = self._parse_playlists(raw)
        self.acestream_server_url = os.environ.get('ACESTREAM_SERVER_URL')
        self.server_port: int = int(os.environ.get('SERVER_PORT', '8000'))
        self.reload_interval: int = int(os.environ.get('RELOAD_INTERVAL', '3600'))
        self.startup_retries: int = int(os.environ.get('STARTUP_RETRIES', '6'))
        self.startup_retry_delay: int = int(os.environ.get('STARTUP_RETRY_DELAY', '5'))

    @staticmethod
    def _parse_playlists(raw: str) -> dict[str, str]:
        result: dict[str, str] = {}
        for entry in raw.split(';'):
            entry = entry.strip()
            if not entry or ':' not in entry:
                continue
            name, url = entry.split(':', 1)
            name, url = name.strip(), url.strip()
            if name and url:
                result[name] = url
        return result


settings = Settings()
