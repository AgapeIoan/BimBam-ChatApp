from pydantic import SecretStr, PostgresDsn
from pydantic_settings import BaseSettings
from typing import Optional

class DatabaseSettings(BaseSettings):
    DB_URL: str
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: SecretStr
    DB_NAME: str