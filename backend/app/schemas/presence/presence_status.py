from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PresenceStatus(BaseModel):
    user_id: UUID = Field(..., alias="userId")
    is_online: bool = Field(..., alias="isOnline")
    last_seen: Optional[datetime] = Field(None, alias="lastSeen")
