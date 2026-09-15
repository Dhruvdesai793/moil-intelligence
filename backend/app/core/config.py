from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MOIL_", env_file=".env", extra="ignore")
    cors_origins: list[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
