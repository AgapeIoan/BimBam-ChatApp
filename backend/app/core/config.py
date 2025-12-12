from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from .settings.auth_settings import AuthSettings
from .settings.database_settings import DatabaseSettings


class Settings(BaseSettings):
    ENV: str = "development"
    LOG_LEVEL: str = "DEBUG"
    DATABASE: DatabaseSettings
    REDIS_URL: str
    OPENAI_API_KEY: str | None = None
    AI_PROVIDER: str = "openai"  # "openai" or "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    AI_MODEL: str = "gpt-4o-mini"
    AUTH: AuthSettings = AuthSettings()

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings() #type: ignore
