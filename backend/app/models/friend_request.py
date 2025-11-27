from datetime import datetime, UTC
from sqlalchemy import ForeignKey, DateTime, UniqueConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from models.enums import FriendRequestStatus


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    status: Mapped[FriendRequestStatus] = mapped_column(
        Enum(FriendRequestStatus, name="friend_request_status"),
        default=FriendRequestStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_friend_request_once"),
    )

    sender = relationship("User", back_populates="sent_requests", foreign_keys=[from_user_id])
    receiver = relationship("User", back_populates="received_requests", foreign_keys=[to_user_id])
