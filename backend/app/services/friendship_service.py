from sqlalchemy.orm import Session

from repositories.friendship_repository import FriendshipRepository
from repositories.user_repository import UserRepository
from core.redis_client import get_online_users
from schemas.user import UserRead


class FriendshipService:

    @staticmethod
    async def get_friends(db: Session, user_id: int):

        friends = FriendshipRepository.get_friends(db, user_id)

        # Get online users from Redis
        online_ids = await get_online_users()

        result = []
        for fr in friends:
            friend = UserRepository.get_by_id(db, fr.friend_id)
            result.append({
                "friend": UserRead.model_validate(friend),
                "is_online": friend.id in online_ids,
                "last_read_message_id": fr.last_read_message_id,
                "unread_count": fr.unread_count,
            })
        return result
