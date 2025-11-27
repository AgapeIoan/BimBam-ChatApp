from sqlalchemy.ext.asyncio import AsyncSession

from repositories.friendship_repository import FriendshipRepository
from repositories.user_repository import UserRepository
from core.redis_client import get_online_users
from schemas.user.user_read import UserRead


class FriendshipService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_friends(self, user_id: int):
        repo = FriendshipRepository(self._session)
        friends = await repo.get_friends(user_id)
        online_ids = await get_online_users()
        user_repo = UserRepository(self._session)
        result = []
        for fr in friends:
            friend = await user_repo.get_by_id(fr.friend_id)
            result.append({
                "friend": UserRead.model_validate(friend),
                "is_online": friend.id in online_ids,
                "last_read_message_id": fr.last_read_message_id,
                "unread_count": fr.unread_count,
            })
        return result
