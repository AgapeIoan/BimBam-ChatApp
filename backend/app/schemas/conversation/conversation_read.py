from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.schemas.conversation_member.conversation_member_read import \
    ConversationMemberRead
from pydantic import BaseModel, ConfigDict


class ConversationRead(BaseModel):
    id: UUID
    is_group: bool
    name: Optional[str] = None
    created_at: datetime

    members: Optional[List[ConversationMemberRead]] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
