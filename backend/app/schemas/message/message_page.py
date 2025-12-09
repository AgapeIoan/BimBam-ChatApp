from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.message.message_read import MessageRead


class MessagePage(BaseModel):
    conversation_id: UUID = Field(..., alias="conversationId")
    messages: List[MessageRead]
    has_more: bool = Field(..., alias="hasMore")
    next_before_id: UUID | None = Field(None, alias="nextBeforeId")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
