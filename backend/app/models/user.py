from datetime import datetime
from typing import Optional, List
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from app.db.base import Base
from app.models.friend_request import FriendRequest
from app.models.message import Message


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    provider: Mapped[str] = mapped_column(String(20)) # e.g., "google", "facebook"
    provider_id: Mapped[str] = mapped_column(String(128), unique=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(120))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    sent_requests: Mapped[List["FriendRequest"]] = relationship(
        "FriendRequest",
        back_populates="sender",
        foreign_keys="FriendRequest.from_user_id"
    )
    received_requests: Mapped[List["FriendRequest"]] = relationship(
        "FriendRequest",
        back_populates="receiver",
        foreign_keys="FriendRequest.to_user_id"
    )

    messages_sent: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="sender",
        foreign_keys="Message.sender_id"
    )
    messages_received: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="receiver",
        foreign_keys="Message.receiver_id"
    )
