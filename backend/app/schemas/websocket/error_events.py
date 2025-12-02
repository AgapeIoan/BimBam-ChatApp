from typing import Optional

from pydantic import BaseModel, Field


class ErrorPayload(BaseModel):
    code: str = Field(..., alias="code")
    detail: str = Field(..., alias="detail")
    correlation_id: Optional[str] = Field(None, alias="correlationId")

    class Config:
        populate_by_name = True
