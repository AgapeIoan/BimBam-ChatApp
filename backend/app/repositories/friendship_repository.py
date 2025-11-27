from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.friendship import Friendship

class FriendshipRepository:
    def __init__(self, session: AsyncSession):
        self._session = session
        
    async def are_friends(self, user_id: int, friend_id: int) -> bool:
        try:
            result = await self._session.execute(
                select(Friendship).where(
                    Friendship.user_id == user_id,
                    Friendship.friend_id == friend_id,
                )
            )
            row = result.scalars().one_or_none()
            return row is not None
        except Exception as e:
            pass

    async def create_friendship_pair(self, user_a: int, user_b: int):
        try:
            f1 = Friendship(user_id=user_a, friend_id=user_b)
            f2 = Friendship(user_id=user_b, friend_id=user_a)
            self._session.add_all([f1, f2])
            await self._session.commit()
            return f1, f2
        except Exception as e:
            pass

    async def get_friends(self, user_id: int) -> List[Friendship]:
        try:
            result = await self._session.execute(
                select(Friendship)
                .where(Friendship.user_id == user_id)
                .order_by(Friendship.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            pass
