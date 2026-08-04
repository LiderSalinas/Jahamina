from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://192.168.0.107:3000,http://192.168.1.20:3000"
    )
    redis_url: str = "redis://localhost:6379/0"
    ws_ticket_expire_seconds: int = 60
    chat_max_message_length: int = 1000
    chat_rate_limit_messages: int = 10
    chat_rate_limit_window_seconds: int = 10
    chat_typing_rate_limit_events: int = 8
    chat_max_payload_bytes: int = 4096
    chat_max_connections_per_user: int = 3
    geocoding_provider_url: str = "https://nominatim.openstreetmap.org"
    routing_provider_url: str = "https://router.project-osrm.org"
    geocoding_api_key: str | None = None
    routing_api_key: str | None = None
    map_request_timeout_seconds: float = 5
    map_cache_ttl_seconds: int = 3600
    location_update_interval_seconds: int = 4
    location_stale_after_seconds: int = 20
    location_max_accuracy_meters: float = 200
    location_rate_limit_updates: int = 5
    location_rate_limit_window_seconds: int = 10
    location_max_payload_bytes: int = 4096
    location_max_connections_per_user: int = 3
    location_eta_cache_seconds: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(
            hide_password=False,
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
