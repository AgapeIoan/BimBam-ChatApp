from uuid import UUID

from pydantic import BaseModel, Field


class TypingStatus(BaseModel):
    from_user_id: UUID = Field(..., alias="fromUserId")
    to_user_id: UUID = Field(..., alias="toUserId")
    is_typing: bool = Field(..., alias="isTyping")
