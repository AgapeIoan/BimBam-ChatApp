from pydantic import BaseModel, Field, EmailStr


class UserResponse(BaseModel):
    email: EmailStr = Field(..., alias="email")
    username: str = Field(..., alias="username")
    avatar_url: str | None = Field(None, alias="avatarUrl")

    class Config:
        from_attributes = True
        populate_by_name = True
