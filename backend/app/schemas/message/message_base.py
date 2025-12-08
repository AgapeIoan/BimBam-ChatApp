from uuid import UUID

from pydantic import BaseModel


class MessageBase(BaseModel):
    conversation_id: UUID
    sender_id: UUID
    content: str
