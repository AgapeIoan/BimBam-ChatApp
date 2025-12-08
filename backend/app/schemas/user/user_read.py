from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.user.user_base import UserBase


class UserRead(UserBase):
    id: UUID = Field(..., alias="id")
    provider: str = Field(..., alias="provider")
    last_seen: datetime = Field(..., alias="lastSeen")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
