from typing import List
from uuid import UUID

from pydantic import BaseModel

from app.schemas.message.message_read import MessageRead


class MessagePage(BaseModel):
    conversation_id: UUID
    messages: List[MessageRead]
    has_more: bool
    next_before_id: UUID | None
