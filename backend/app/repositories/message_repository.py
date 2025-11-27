from typing import List, Optional
from datetime import datetime, UTC

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from models.message import Message


class MessageRepository:
    @staticmethod
    def create(
        db: Session,
        *,
        sender_id: int,
        receiver_id: int,
        body: str,
    ) -> Message:

        msg = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            body=body,
            created_at=datetime.now(UTC),
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def get_conversation(
        db: Session,
        *,
        user_id: int,
        with_user_id: int,
        limit: int = 100,
        before_id: Optional[int] = None,
    ) -> List[Message]:

        q = db.query(Message).filter(
            or_(
                and_(
                    Message.sender_id == user_id,
                    Message.receiver_id == with_user_id,
                ),
                and_(
                    Message.sender_id == with_user_id,
                    Message.receiver_id == user_id,
                ),
            )
        )

        if before_id is not None:
            # Only messages older than a given id
            q = q.filter(Message.id < before_id)

        q = q.order_by(Message.created_at.asc()).limit(limit)
        return q.all()

    @staticmethod
    def get_unread_from_user(
        db: Session,
        *,
        receiver_id: int,
        from_user_id: int,
    ) -> List[Message]:

        return (
            db.query(Message)
            .filter(
                Message.sender_id == from_user_id,
                Message.receiver_id == receiver_id,
                Message.read.is_(False),
            )
            .order_by(Message.created_at.asc())
            .all()
        )

    @staticmethod
    def mark_messages_as_read(
        db: Session,
        *,
        receiver_id: int,
        from_user_id: int,
    ) -> List[Message]:
        """
        Mark all unread messages from from_user_id → receiver_id as read.
        Returns the list of affected messages.
        """
        messages = MessageRepository.get_unread_from_user(
            db,
            receiver_id=receiver_id,
            from_user_id=from_user_id,
        )

        if not messages:
            return []

        for m in messages:
            m.read = True

        db.commit()
        return messages
