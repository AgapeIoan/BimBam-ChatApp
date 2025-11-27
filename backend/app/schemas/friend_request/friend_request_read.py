from datetime import datetime
from pydantic import BaseModel, Field

class FriendRequestRead(BaseModel):
    id: int = Field(..., alias="id")
    from_user_id: int = Field(..., alias="fromUserId")
    to_user_id: int = Field(..., alias="toUserId")
    status: str = Field(..., alias="status")
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        from_attributes = True
