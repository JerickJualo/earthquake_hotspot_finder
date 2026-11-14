"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime configuration for local development and deployment."""

    app_name: str = "Earthquake Hotspot Finder API"
    app_env: str = "development"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    database_url: str = (
        "postgresql+psycopg://postgres:CHANGE_ME@localhost:5432/"
        "earthquake_hotspot_finder"
    )
    allowed_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Return configured CORS origins as a clean list."""

        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
