from datetime import datetime
from pydantic import BaseModel


class FriendshipRead(BaseModel):
    id: int
    user_id: int
    friend_id: int
    created_at: datetime
    last_read_message_id: int | None
    unread_count: int

    class Config:
        from_attributes = True
