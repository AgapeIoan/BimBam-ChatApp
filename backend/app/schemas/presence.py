from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PresenceStatus(BaseModel):
    user_id: int
    is_online: bool
    last_seen: Optional[datetime] = None


class TypingStatus(BaseModel):
    from_user_id: int
    to_user_id: int
    is_typing: bool
