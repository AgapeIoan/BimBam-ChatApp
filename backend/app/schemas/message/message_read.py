from datetime import datetime
from typing import Optional
from uuid import UUID

from app.schemas.user.user_read import UserRead
from pydantic import BaseModel, ConfigDict, Field


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    conversation_id: UUID = Field(..., alias="conversationId")

    sender_id: UUID = Field(..., alias="senderId")
    sender: Optional[UserRead] = None  # loaded when needed

    content: str
    created_at: datetime = Field(..., alias="createdAt")

    delivered: bool
    read: bool
    edited_at: datetime | None = Field(None, alias="editedAt")
    edited_by_id: UUID | None = Field(None, alias="editedById")