from datetime import datetime, UTC
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Friendship(Base):
    __tablename__ = "friendships"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    friend_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))

    # synced from Redis periodically
    last_read_message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unread_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("user_id", "friend_id", name="uq_friendship_pair"),
    )
