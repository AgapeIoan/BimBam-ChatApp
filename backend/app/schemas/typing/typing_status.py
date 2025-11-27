from pydantic import BaseModel, Field

class TypingStatus(BaseModel):
    from_user_id: int = Field(..., alias="fromUserId")
    to_user_id: int = Field(..., alias="toUserId")
    is_typing: bool = Field(..., alias="isTyping")
