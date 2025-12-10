from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.schemas.user.user_read import UserRead
from pydantic import BaseModel, ConfigDict, Field


class ConversationPreview(BaseModel):
    id: UUID
    is_group: bool
    name: Optional[str]

    # Shown in chat list
    last_message: Optional[str]
    last_message_at: Optional[datetime]

    # For direct chats (DM)
    other_users: List[UserRead] = Field(default_factory=list)

    # For unread badge
    unread_count: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
