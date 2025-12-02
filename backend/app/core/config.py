from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from .settings.database_settings import DatabaseSettings
from .settings.auth_settings import AuthSettings

class Settings(BaseSettings):
    ENV: str = "development"
    LOG_LEVEL: str = "DEBUG"
    DATABASE: DatabaseSettings
    REDIS_URL: str
    AUTH: AuthSettings

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")


@lru_cache
def get_settings() -> Settings:
    return Settings()
