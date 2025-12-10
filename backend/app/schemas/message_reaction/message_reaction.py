from __future__ import annotations

from datetime import datetime
from typing import Dict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReactionCreate(BaseModel):
    emoji: str

    model_config = ConfigDict(extra="forbid")


class ReactionRead(BaseModel):
    id: UUID
    message_id: UUID = Field(..., alias="messageId")
    user_id: UUID = Field(..., alias="userId")
    emoji: str
    created_at: datetime = Field(..., alias="createdAt")

    model_config = ConfigDict(from_attributes=True)


class ReactionCounts(BaseModel):
    message_id: UUID = Field(..., alias="messageId")
    counts: Dict[str, int] # for example: {"👍": 3, "❤️": 5}

    model_config = ConfigDict(from_attributes=True)
