from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    FRONTEND_ORIGIN: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AUTH__",
        env_nested_delimiter="__",
        extra="ignore",
    )
