from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class EventEnvelope(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(..., alias="type")
    data: Dict[str, Any] = Field(default_factory=dict, alias="data")
    correlation_id: Optional[str] = Field(None, alias="correlationId")
    timestamp: Optional[datetime] = Field(None, alias="timestamp")
