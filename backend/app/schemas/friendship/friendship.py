from datetime import datetime
from pydantic import BaseModel, Field

class FriendshipRead(BaseModel):
    id: int = Field(..., alias="id")
    user_id: int = Field(..., alias="userId")
    friend_id: int = Field(..., alias="friendId")
    created_at: datetime = Field(..., alias="createdAt")
    last_read_message_id: int | None = Field(None, alias="lastReadMessageId")
    unread_count: int = Field(..., alias="unreadCount")

    class Config:
        from_attributes = True
        populate_by_name = True
