from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from app.schemas.user.user_read import UserRead


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    conversation_id: UUID

    sender_id: UUID
    sender: Optional[UserRead] = None  # loaded when needed

    content: str
    created_at: datetime

    delivered: bool
    read: bool
