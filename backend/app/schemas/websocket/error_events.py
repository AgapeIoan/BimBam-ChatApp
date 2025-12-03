from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ErrorPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., alias="code")
    detail: str = Field(..., alias="detail")
    correlation_id: Optional[str] = Field(None, alias="correlationId")
