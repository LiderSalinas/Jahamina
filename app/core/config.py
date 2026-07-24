from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, Field


class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn = Field(..., alias="DATABASE_URL")  # <-- clave
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = 30

    class Config:
        extra = "forbid"
        allow_population_by_field_name = True  # permite acceder como `settings.DATABASE_URL`

settings = Settings()
