from datetime import datetime
from pydantic import Field
from schemas.user.user_base import UserBase

class UserRead(UserBase):
    id: int = Field(..., alias="id")
    provider: str = Field(..., alias="provider")
    last_seen: datetime = Field(..., alias="lastSeen")

    class Config:
        from_attributes = True
        populate_by_name = True
