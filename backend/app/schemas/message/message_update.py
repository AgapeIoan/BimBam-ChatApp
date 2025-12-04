from pydantic import BaseModel


class MessageUpdate(BaseModel):
    content: str
