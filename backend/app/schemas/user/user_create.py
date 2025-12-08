from typing import Optional

from pydantic import EmailStr, Field

from app.schemas.user.user_base import UserBase


class UserCreate(UserBase):
    provider: str = Field(..., alias="provider")
    provider_id: str = Field(..., alias="providerId")
    email: EmailStr = Field(..., alias="email")
    username: str = Field(..., alias="username")
    avatar_url: Optional[str] = Field(None, alias="avatarUrl")
