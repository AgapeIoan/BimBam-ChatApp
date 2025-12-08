from uuid import UUID

from pydantic import BaseModel


class MessageCreate(BaseModel):
    conversation_id: UUID
    content: str
