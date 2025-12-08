from datetime import datetime
from typing import Optional
from uuid import UUID

from app.schemas.user.user_read import UserRead
from pydantic import BaseModel


class ConversationMemberRead(BaseModel):
    id: UUID
    conversation_id: UUID
    user: UserRead
    joined_at: datetime
    last_read_message_id: Optional[UUID]
    unread_count: int
    is_admin: bool
    is_muted: bool

    class Config:
        from_attributes = True
