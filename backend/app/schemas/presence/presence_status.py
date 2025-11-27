from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PresenceStatus(BaseModel):
    user_id: int = Field(..., alias="userId")
    is_online: bool = Field(..., alias="isOnline")
    last_seen: Optional[datetime] = Field(None, alias="lastSeen")
