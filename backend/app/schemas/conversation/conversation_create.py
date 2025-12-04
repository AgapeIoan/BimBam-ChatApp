from pydantic import BaseModel
from typing import List
from uuid import UUID


class ConversationCreate(BaseModel):
    name: str
    member_ids: List[UUID]  # users to add into the group
