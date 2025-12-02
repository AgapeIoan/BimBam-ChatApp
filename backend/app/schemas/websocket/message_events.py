from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class MessageSendPayload(BaseModel):
    conversation_id: UUID = Field(..., alias="conversationId")
    content: str

    class Config:
        populate_by_name = True


class MessageDeliveredPayload(BaseModel):
    message_id: UUID = Field(..., alias="messageId")
    conversation_id: UUID = Field(..., alias="conversationId")
    sender_id: UUID = Field(..., alias="senderId")
    content: str
    created_at: datetime = Field(..., alias="createdAt")
    delivered: bool = Field(..., alias="delivered")
    read: bool = Field(..., alias="read")

    class Config:
        populate_by_name = True


class MessageAckPayload(BaseModel):
    correlation_id: Optional[str] = Field(None, alias="correlationId")
    message_id: Optional[UUID] = Field(None, alias="messageId")
    status: str
    delivered: bool = Field(default=False, alias="delivered")
    message: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        populate_by_name = True
