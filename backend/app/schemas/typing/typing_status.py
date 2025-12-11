from uuid import UUID

from pydantic import BaseModel, Field


class TypingStatus(BaseModel):
    from_user_id: UUID = Field(..., alias="fromUserId")
    to_user_id: UUID | None = Field(None, alias="toUserId")
    conversation_id: UUID | None = Field(None, alias="conversationId")
    is_typing: bool = Field(..., alias="isTyping")
