from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class FriendshipRead(BaseModel):
    id: UUID = Field(..., alias="id")
    user_id: UUID = Field(..., alias="userId")
    friend_id: UUID = Field(..., alias="friendId")
    created_at: datetime = Field(..., alias="createdAt")
    last_read_message_id: UUID | None = Field(None, alias="lastReadMessageId")
    unread_count: int = Field(..., alias="unreadCount")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
