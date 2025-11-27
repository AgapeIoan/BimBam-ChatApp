from datetime import datetime
from pydantic import BaseModel, Field

class MessageRead(BaseModel):
    id: int = Field(..., alias="id")
    sender_id: int = Field(..., alias="senderId")
    receiver_id: int = Field(..., alias="receiverId")
    content: str = Field(..., alias="content")
    created_at: datetime = Field(..., alias="createdAt")
    delivered: bool = Field(..., alias="delivered")
    read: bool = Field(..., alias="read")

    class Config:
        from_attributes = True
