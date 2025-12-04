from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID

from schemas.conversation_member.conversation_member_read import ConversationMemberRead


class ConversationRead(BaseModel):
    id: UUID
    is_group: bool
    name: Optional[str] = None
    created_at: datetime

    members: Optional[List[ConversationMemberRead]] = None

    class Config:
        from_attributes = True
