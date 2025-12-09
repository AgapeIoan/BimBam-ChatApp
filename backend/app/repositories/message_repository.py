from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.message import Message
from app.models.message_edit import MessageEdit


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        *,
        conversation_id: UUID,
        sender_id: UUID,
        content: str,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
        )

        self._session.add(msg)
        await self._session.flush()
        await self._session.refresh(msg)
        return msg

    async def get_messages(
        self,
        *,
        conversation_id: UUID,
        limit: int = 50,
        before_id: Optional[UUID] = None,
    ) -> List[Message]:
        # Base query: all messages from the conversation
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .options(selectinload(Message.sender))  # preload sender user
        )

        if before_id:
            # Find timestamp of the before_id message
            before_msg = await self.get_by_id(before_id)
            if before_msg:
                query = query.where(Message.created_at < before_msg.created_at)

        result = await self._session.execute(query)
        messages = list(result.scalars().all())

        messages.reverse()
        return messages

    async def get_by_id(self, message_id: UUID) -> Optional[Message]:
        result = await self._session.execute(
            select(Message).where(Message.id == message_id).options(selectinload(Message.sender))
        )
        return result.scalars().one_or_none()

    async def mark_messages_as_read(
        self,
        conversation_id: UUID,
        user_id: UUID,
        before_message_id: Optional[UUID] = None,
    ) -> List[Message]:
        # Get messages that were sent by other users
        query = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.sender_id != user_id,
                Message.read.is_(False),
            )
            .order_by(Message.created_at.asc())
        )

        if before_message_id:
            before_msg = await self.get_by_id(before_message_id)
            if before_msg:
                query = query.where(Message.created_at <= before_msg.created_at)

        result = await self._session.execute(query)
        unread_messages = result.scalars().all()

        # Mark them as read
        for msg in unread_messages:
            msg.read = True

        if unread_messages:
            await self._session.flush()

        return unread_messages

    async def mark_delivered(self, message_id: UUID) -> Optional[Message]:
        """
        Mark a message as delivered.
        """
        msg = await self.get_by_id(message_id)
        if not msg:
            return None
        msg.delivered = True
        await self._session.flush()
        await self._session.refresh(msg)
        return msg

    async def edit_message(self, message_id: UUID, editor_id: UUID, new_content: str):
        msg = await self.get_by_id(message_id)
        if not msg:
            return None, None

        old_content = msg.content
        msg.content = new_content
        # record edit metadata on the message itself
        msg.edited_at = datetime.now(timezone.utc)
        msg.edited_by_id = editor_id

        edit_record = MessageEdit(
            message_id=message_id,
            editor_id=editor_id,
            old_content=old_content,
            new_content=new_content,
        )

        self._session.add(edit_record)
        await self._session.flush()
        await self._session.refresh(msg)
        await self._session.refresh(edit_record)

        return msg, edit_record

    async def delete_message(self, message_id: UUID) -> bool:
        msg = await self.get_by_id(message_id)
        if not msg:
            return False
        await self._session.delete(msg)
        await self._session.flush()
        return True
