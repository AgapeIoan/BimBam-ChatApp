from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    GOOGLE_CLIENT_ID: str = "dummy-google-client-id"
    GOOGLE_CLIENT_SECRET: str = "dummy-google-client-secret"

    JWT_SECRET_KEY: str = "change_me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AUTH__",
        env_nested_delimiter="__",
        extra="ignore",
    )
