from typing import Dict, List
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message_reaction import MessageReaction
from app.models.user import User


class MessageReactionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_reaction(self, message_id: UUID, user_id: UUID, emoji: str) -> MessageReaction:
        # Avoid integrity errors by checking first
        q = select(MessageReaction).where(
            MessageReaction.message_id == message_id,
            MessageReaction.user_id == user_id,
            MessageReaction.emoji == emoji,
        )
        result = await self._session.execute(q)
        existing = result.scalars().one_or_none()
        if existing:
            return existing

        reaction = MessageReaction(message_id=message_id, user_id=user_id, emoji=emoji)
        self._session.add(reaction)
        try:
            await self._session.flush()
            await self._session.refresh(reaction)
            return reaction
        except IntegrityError:
            # If a race inserted it, fetch and return that one
            await self._session.rollback()
            result = await self._session.execute(q)
            existing = result.scalars().one_or_none()
            if existing:
                return existing
            raise

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

    async def get_counts_for_messages(self, message_ids: list[UUID]) -> Dict[UUID, Dict[str, int]]:
        if not message_ids:
            return {}
        q = (
            select(MessageReaction.message_id, MessageReaction.emoji, func.count(MessageReaction.id))
            .where(MessageReaction.message_id.in_(message_ids))
            .group_by(MessageReaction.message_id, MessageReaction.emoji)
        )
        result = await self._session.execute(q)
        counts: Dict[UUID, Dict[str, int]] = {}
        for mid, emoji, cnt in result:
            mid = UUID(str(mid))
            counts.setdefault(mid, {})[emoji] = int(cnt)
        return counts

    async def get_usernames_grouped_by_emoji(self, message_id: UUID) -> Dict[str, List[str]]:
        """
        Return a mapping of emoji -> list of usernames who reacted with that emoji
        for the given message.
        """
        q = (
            select(MessageReaction.emoji, User.username)
            .join(User, User.id == MessageReaction.user_id)
            .where(MessageReaction.message_id == message_id)
            .order_by(MessageReaction.emoji.asc(), User.username.asc())
        )
        result = await self._session.execute(q)
        rows = result.all()
        grouped: Dict[str, List[str]] = {}
        for emoji, username in rows:
            grouped.setdefault(emoji, []).append(username)
        return grouped
