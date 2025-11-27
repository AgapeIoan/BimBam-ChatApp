
from typing import List, Optional
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from models.message import Message

class MessageRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        *,
        sender_id: int,
        receiver_id: int,
        content: str,
    ) -> Message:
        try:
            msg = Message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                created_at=datetime.now(UTC),
            )
            self._session.add(msg)
            await self._session.commit()
            await self._session.refresh(msg)
            return msg
        except Exception as e:
            pass

    async def get_conversation(
        self,
        *,
        user_id: int,
        with_user_id: int,
        limit: int = 100,
        before_id: Optional[int] = None,
    ) -> List[Message]:
        try:
            stmt = select(Message).where(
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
                stmt = stmt.where(Message.id < before_id)
            stmt = stmt.order_by(Message.created_at.asc()).limit(limit)
            result = await self._session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            pass

    async def get_unread_from_user(
        self,
        *,
        receiver_id: int,
        from_user_id: int,
    ) -> List[Message]:

        return (
            self._session.query(Message)
            .filter(
                Message.sender_id == from_user_id,
                Message.receiver_id == receiver_id,
                Message.read.is_(False),
            )
            .order_by(Message.created_at.asc())
            .all()
        )

    async def mark_messages_as_read(
        self,
        *,
        receiver_id: int,
        from_user_id: int,
    ) -> List[Message]:
        """
        Mark all unread messages from from_user_id → receiver_id as read.
        Returns the list of affected messages.
        """
        messages = await self.get_unread_from_user(
            receiver_id=receiver_id,
            from_user_id=from_user_id,
        )

        if not messages:
            return []

        for m in messages:
            m.read = True

        await self._session.commit()
        return messages
