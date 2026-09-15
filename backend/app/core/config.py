from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "MOIL Intelligence API"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = Field(
        default="postgresql+psycopg://moil:moil_dev_password@localhost:5432/moil_intelligence", repr=False)
    gee_enabled: bool = False
    gee_project_id: str = "secure-guru-473417-q2"
    gee_auth_method: str = "oauth"
    gee_allow_demo_features: bool = True
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:8501", "http://127.0.0.1:8501"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value):
        return [item.strip() for item in value.split(",") if item.strip()] if isinstance(value, str) else value


@lru_cache
def get_settings() -> Settings:
    return Settings()
