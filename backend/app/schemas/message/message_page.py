from typing import List
from uuid import UUID

from app.schemas.message.message_read import MessageRead
from pydantic import BaseModel


class MessagePage(BaseModel):
    conversation_id: UUID
    messages: List[MessageRead]
    has_more: bool
    next_before_id: UUID | None
