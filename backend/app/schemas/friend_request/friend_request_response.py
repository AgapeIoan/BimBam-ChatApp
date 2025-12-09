# app/schemas/friend_request/friend_request_response.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.enums import FriendRequestStatus
from app.schemas.user.user_response import UserResponse


class FriendRequestResponse(BaseModel):
    id: UUID = Field(..., alias="id")
    status: FriendRequestStatus = Field(..., alias="status")
    created_at: datetime = Field(..., alias="createdAt")

    sender: UserResponse = Field(..., alias="fromUser")
    receiver: UserResponse = Field(..., alias="toUser")

    class Config:
        from_attributes = True
        populate_by_name = True
