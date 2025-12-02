from pydantic import BaseModel
from uuid import UUID


class MessageBase(BaseModel):
    conversation_id: UUID
    sender_id: UUID
    content: str
