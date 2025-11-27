from pydantic import BaseModel, Field

class FriendRequestCreate(BaseModel):
    to_email: str = Field(..., alias="toEmail")
