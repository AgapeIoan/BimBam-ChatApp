from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class MessageSendPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    conversation_id: UUID = Field(..., alias="conversationId")
    content: str


class MessageEditPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message_id: UUID = Field(..., alias="messageId")
    content: str


class MessageReactionPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message_id: UUID = Field(..., alias="messageId")
    emoji: str
    action: Literal["add", "remove"]


class MessageDeliveredPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message_id: UUID = Field(..., alias="messageId")
    conversation_id: UUID = Field(..., alias="conversationId")
    sender_id: UUID = Field(..., alias="senderId")
    content: str
    created_at: datetime = Field(..., alias="createdAt")
    delivered: bool = Field(..., alias="delivered")
    read: bool = Field(..., alias="read")
    edited_at: Optional[datetime] = Field(None, alias="editedAt")
    edited_by_id: Optional[UUID] = Field(None, alias="editedById")


class MessageAckPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    correlation_id: Optional[str] = Field(None, alias="correlationId")
    message_id: Optional[UUID] = Field(None, alias="messageId")
    status: str
    delivered: bool = Field(default=False, alias="delivered")
    message: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
