from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    JWT_SECRET: str = "change_me"
    JWT_ALGORITHM: str = "HS256"
