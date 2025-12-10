from uuid import UUID

from app.core.redis_client import get_online_users
from app.repositories.friendship_repository import FriendshipRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user.user_read import UserRead


class FriendshipService:
    def __init__(
        self,
        friendship_repo: FriendshipRepository,
        user_repo: UserRepository,
    ):
        self.friendship_repo = friendship_repo
        self.user_repo = user_repo

    async def are_friends(self, user_id: UUID, friend_id: UUID) -> bool:
        """
        Lightweight helper that proxies to the repository to check whether two users
        are friends in either direction.
        """
        return await self.friendship_repo.are_friends(user_id, friend_id)

    async def get_friends(self, user_id: UUID):
        friends = await self.friendship_repo.get_friends(user_id)
        online_ids = await get_online_users()
        result = []
        for fr in friends:
            friend = await self.user_repo.get_by_id(fr.friend_id)
            if not friend:
                continue  
            result.append(
                {
                    "friend": UserRead.model_validate(friend),
                    "is_online": str(friend.id) in online_ids,
                    "last_read_message_id": fr.last_read_message_id,
                    "unread_count": fr.unread_count,
                }
            )
        return result
