from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    playlist_urls: str = ""
    playlist_url: str = ""  # legacy single-playlist setting
    acestream_server_url: str | None = None
    server_port: int = 8000
    reload_interval: int = 3600
    startup_retries: int = 6
    startup_retry_delay: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def playlists(self) -> dict[str, str]:
        """Parse configured playlists, falling back to the legacy setting."""
        raw = self.playlist_urls
        if not raw and self.playlist_url:
            raw = f"hashes:{self.playlist_url}"
        return self._parse_playlists(raw)

    @staticmethod
    def _parse_playlists(raw: str) -> dict[str, str]:
        result: dict[str, str] = {}
        for entry in raw.split(";"):
            entry = entry.strip()
            if not entry or ":" not in entry:
                continue
            name, url = entry.split(":", 1)
            name, url = name.strip(), url.strip()
            if name and url:
                result[name] = url
        return result

    def validate_runtime(self) -> None:
        """Fail fast when required runtime configuration is missing."""
        url = self.acestream_server_url
        if not url or "{hash}" not in url:
            raise ValueError(
                "ACESTREAM_SERVER_URL must be set and contain the '{hash}' placeholder"
            )


settings = Settings()
