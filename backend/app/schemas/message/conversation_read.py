from typing import List
from pydantic import BaseModel, Field
from message_read import MessageRead

class ConversationRead(BaseModel):
    with_user_id: int = Field(..., alias="withUserId")
    messages: List[MessageRead] = Field(..., alias="messages")
