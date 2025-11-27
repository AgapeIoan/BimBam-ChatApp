from sqlalchemy.ext.asyncio import AsyncSession

from repositories.friendship_repository import FriendshipRepository
from repositories.user_repository import UserRepository
from core.redis_client import get_online_users
from schemas.user.user_read import UserRead


class FriendshipService:
    def __init__(
        self,
        friendship_repo: FriendshipRepository,
        user_repo: UserRepository,
    ):
        self.friendship_repo = friendship_repo
        self.user_repo = user_repo

    async def get_friends(self, user_id: int):
        try:
            friends = await self.friendship_repo.get_friends(user_id)
            online_ids = await get_online_users()
            result = []
            for fr in friends:
                friend = await self.user_repo.get_by_id(fr.friend_id)
                result.append({
                    "friend": UserRead.model_validate(friend),
                    "is_online": friend.id in online_ids,
                    "last_read_message_id": fr.last_read_message_id,
                    "unread_count": fr.unread_count,
                })
            return result
        except Exception as e:
            pass
