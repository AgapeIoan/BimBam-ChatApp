from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr = Field(..., alias="email")
    username: str = Field(..., alias="username")
    avatar_url: Optional[str] = Field(None, alias="avatarUrl")
