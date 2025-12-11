from typing import Optional

from app.schemas.user.user_base import UserBase
from pydantic import EmailStr, Field


class UserCreate(UserBase):
    provider: str = Field(..., alias="provider")
    provider_id: str = Field(..., alias="providerId")
    email: EmailStr = Field(..., alias="email")
    username: str = Field(..., alias="username")
    avatar_url: Optional[str] = Field(None, alias="avatarUrl")
