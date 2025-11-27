from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class MessageCreate(BaseModel):
    receiver_id: int
    content: str


class MessageRead(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    created_at: datetime
    delivered: bool
    read: bool

    class Config:
        from_attributes = True


class ConversationRead(BaseModel):
    with_user_id: int
    messages: List[MessageRead]
