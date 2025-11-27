from pydantic import BaseModel, Field

class MessageCreate(BaseModel):
    receiver_id: int = Field(..., alias="receiverId")
    content: str = Field(..., alias="content")


