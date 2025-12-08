from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import FriendRequestStatus


class FriendRequestRead(BaseModel):
    id: UUID = Field(..., alias="id")
    from_user_id: UUID = Field(..., alias="fromUserId")
    to_user_id: UUID = Field(..., alias="toUserId")
    status: FriendRequestStatus = Field(..., alias="status")
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True
