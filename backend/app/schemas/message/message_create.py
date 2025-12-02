from pydantic import BaseModel
from uuid import UUID


class MessageCreate(BaseModel):
    conversation_id: UUID
    content: str
