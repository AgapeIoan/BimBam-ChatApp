from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    id: UUID = Field(..., alias="id")
    email: EmailStr = Field(..., alias="email")
    username: str = Field(..., alias="username")
    avatar_url: str | None = Field(None, alias="avatarUrl")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
