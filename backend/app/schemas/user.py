from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    username: str
    avatar_url: Optional[str] = None


class UserCreate(BaseModel):
    provider: str
    provider_id: str
    email: EmailStr
    username: str
    avatar_url: Optional[str] = None


class UserRead(UserBase):
    id: int
    provider: str
    last_seen: datetime

    class Config:
        from_attributes = True
