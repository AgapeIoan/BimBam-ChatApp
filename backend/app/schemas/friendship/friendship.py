from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.user.user_read import UserRead


class FriendshipRead(BaseModel):
    id: UUID = Field(..., alias="id")
    user_id: UUID = Field(..., alias="userId")
    friend_id: UUID = Field(..., alias="friendId")
    created_at: datetime = Field(..., alias="createdAt")
    last_read_message_id: UUID | None = Field(None, alias="lastReadMessageId")
    unread_count: int = Field(..., alias="unreadCount")

    class Config:
        from_attributes = True
        populate_by_name = True

class FriendListItem(BaseModel):
    friend: UserRead
    is_online: bool = Field(..., alias="isOnline")
    last_read_message_id: Optional[UUID] = Field(None, alias="lastReadMessageId")
    unread_count: int = Field(..., alias="unreadCount")

    class Config:
        from_attributes = True
        populate_by_name = True