import uuid
from datetime import datetime

from app.db.base import Base
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    is_group: Mapped[bool] = mapped_column(Boolean, default=False)

    # Only used for groups
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    members = relationship(
        "ConversationMember", back_populates="conversation", cascade="all, delete-orphan"
    )
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
