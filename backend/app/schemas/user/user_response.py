from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    email: EmailStr = Field(..., alias="email")
    username: str = Field(..., alias="username")
    avatar_url: str | None = Field(None, alias="avatarUrl")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
