from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageEditCreate(BaseModel):
    content: str

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class MessageEditRead(BaseModel):
    id: UUID
    message_id: UUID = Field(..., alias="messageId")
    editor_id: Optional[UUID] = Field(None, alias="editorId")
    old_content: str = Field(..., alias="oldContent")
    new_content: str = Field(..., alias="newContent")
    reason: Optional[str] = None
    created_at: datetime = Field(..., alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
