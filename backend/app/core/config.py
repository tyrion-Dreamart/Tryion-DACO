from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME: str = "DACO ERP"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str
    ANTHROPIC_API_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Hosts permitidos para TrustedHostMiddleware en producción.
    # Si se deja vacío, se derivan automáticamente de los hostnames de ALLOWED_ORIGINS.
    ALLOWED_HOSTS: str = ""

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v) -> str:
        if isinstance(v, list):
            return ",".join(v)
        return str(v)

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        if self.ALLOWED_HOSTS.strip():
            return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]
        hosts = {urlparse(origin.strip()).hostname for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()}
        return [h for h in hosts if h]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()