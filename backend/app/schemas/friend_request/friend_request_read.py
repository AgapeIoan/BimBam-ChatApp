from datetime import datetime
from uuid import UUID

from app.models.enums import FriendRequestStatus
from pydantic import BaseModel, ConfigDict, Field


class FriendRequestRead(BaseModel):
    id: UUID = Field(..., alias="id")
    from_user_id: UUID = Field(..., alias="fromUserId")
    to_user_id: UUID = Field(..., alias="toUserId")
    status: FriendRequestStatus = Field(..., alias="status")
    created_at: datetime = Field(..., alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
