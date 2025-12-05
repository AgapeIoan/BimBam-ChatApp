from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    JWT_SECRET: str = "change_me"
    JWT_ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AUTH__",
        env_nested_delimiter="__",
        extra="ignore",
    )
