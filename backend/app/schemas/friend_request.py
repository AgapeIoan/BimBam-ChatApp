from datetime import datetime
from pydantic import BaseModel


class FriendRequestRead(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FriendRequestCreate(BaseModel):
    to_email: str
