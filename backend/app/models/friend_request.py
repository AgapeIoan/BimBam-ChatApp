from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, UniqueConstraint, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from backend.app.db.base_class import Base
from backend.app.models.enums import FriendRequestStatus


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    from_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    to_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    status: Mapped[FriendRequestStatus] = mapped_column(
        Enum(FriendRequestStatus, name="friend_request_status"),
        default=FriendRequestStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_friend_request_once"),
    )

    sender = relationship("User", back_populates="sent_requests", foreign_keys=[from_user_id])
    receiver = relationship("User", back_populates="received_requests", foreign_keys=[to_user_id])
