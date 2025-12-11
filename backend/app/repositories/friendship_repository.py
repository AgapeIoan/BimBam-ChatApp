from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.friendship import Friendship


class FriendshipRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def are_friends(self, user_id: UUID, friend_id: UUID) -> bool:
        result = await self._session.execute(
            select(Friendship).where(
                Friendship.user_id == user_id,
                Friendship.friend_id == friend_id,
            )
        )
        row = result.scalars().one_or_none()
        return row is not None

    async def create_friendship_pair(self, user_a: UUID, user_b: UUID):
        f1 = Friendship(user_id=user_a, friend_id=user_b)
        f2 = Friendship(user_id=user_b, friend_id=user_a)

        self._session.add_all([f1, f2])

        await self._session.flush()
        await self._session.refresh(f1)
        await self._session.refresh(f2)

        return f1, f2

    async def get_friends(self, user_id: UUID) -> List[Friendship]:
        result = await self._session.execute(
            select(Friendship)
            .where(Friendship.user_id == user_id)
            .order_by(Friendship.created_at.desc())
        )
        return result.scalars().all()
