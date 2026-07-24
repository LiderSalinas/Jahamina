from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: str
    access_token_expire_minutes: int = 30
    secret_key: str = "mi_super_clave_secreta_123"  
    algorithm: str = "HS256"                        

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:"
            f"{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/"
            f"{self.postgres_db}"
        )

    class Config:
        extra = "allow"  # Esto permite ignorar variables no definidas en desarrollo


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
