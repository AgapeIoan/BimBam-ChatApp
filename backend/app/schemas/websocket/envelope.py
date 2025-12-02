from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    type: str = Field(..., alias="type")
    data: Dict[str, Any] = Field(default_factory=dict, alias="data")
    correlation_id: Optional[str] = Field(None, alias="correlationId")
    timestamp: Optional[datetime] = Field(None, alias="timestamp")

    class Config:
        populate_by_name = True
