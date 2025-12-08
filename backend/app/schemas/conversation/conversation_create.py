from typing import List
from uuid import UUID

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    name: str
    member_ids: List[UUID]  # users to add into the group
