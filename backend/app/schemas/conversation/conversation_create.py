from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_name: str = Field(..., alias="groupName")
    participant_ids: List[UUID] = Field(..., alias="participantIds")
