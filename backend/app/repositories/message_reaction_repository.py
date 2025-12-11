from typing import Dict, List
from uuid import UUID

from app.models.message_reaction import MessageReaction
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class MessageReactionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_reaction(self, message_id: UUID, user_id: UUID, emoji: str) -> MessageReaction:
        reaction = MessageReaction(message_id=message_id, user_id=user_id, emoji=emoji)
        self._session.add(reaction)
        await self._session.flush()
        await self._session.refresh(reaction)
        return reaction

    async def remove_reaction(self, message_id: UUID, user_id: UUID, emoji: str) -> bool:
        q = select(MessageReaction).where(
            MessageReaction.message_id == message_id,
            MessageReaction.user_id == user_id,
            MessageReaction.emoji == emoji,
        )
        result = await self._session.execute(q)
        r = result.scalars().one_or_none()
        if not r:
            return False
        await self._session.delete(r)
        await self._session.flush()
        return True

    async def get_reaction_counts(self, message_id: UUID) -> Dict[str, int]:
        # Count reactions grouped by emoji
        q = select(MessageReaction.emoji, func.count(MessageReaction.id)).where(
            MessageReaction.message_id == message_id
        ).group_by(MessageReaction.emoji)

        result = await self._session.execute(q)
        rows = result.all()
        return {row[0]: int(row[1]) for row in rows}

    async def get_reactions(self, message_id: UUID) -> List[MessageReaction]:
        q = select(MessageReaction).where(MessageReaction.message_id == message_id).order_by(MessageReaction.created_at.asc())
        result = await self._session.execute(q)
        return result.scalars().all()
