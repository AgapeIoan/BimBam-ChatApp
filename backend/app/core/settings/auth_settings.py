from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    JWT_SECRET: str = "change_me"
    JWT_ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(extra="ignore")
