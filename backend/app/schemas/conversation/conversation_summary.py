from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ConversationSummaryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    hours: Optional[int] = Field(None, ge=1, le=168)


class ConversationSummaryResponse(BaseModel):
    summary: str
