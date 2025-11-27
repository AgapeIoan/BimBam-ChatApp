from datetime import datetime
from pydantic import BaseModel, Field
from models.enums import FriendRequestStatus

class FriendRequestRead(BaseModel):
    id: int = Field(..., alias="id")
    from_user_id: int = Field(..., alias="fromUserId")
    to_user_id: int = Field(..., alias="toUserId")
    status: FriendRequestStatus = Field(..., alias="status")
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True
