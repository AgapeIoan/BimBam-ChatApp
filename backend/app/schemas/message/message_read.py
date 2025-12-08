from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from app.schemas.user.user_read import UserRead


class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID

    sender_id: UUID
    sender: Optional[UserRead] = None  # loaded when needed

    content: str
    created_at: datetime

    delivered: bool
    read: bool

    class Config:
        from_attributes = True
