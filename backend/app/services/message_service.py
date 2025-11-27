from typing import List, Optional

from models.friendship import Friendship
from models.message import Message
from sqlalchemy import select
from repositories.message_repository import MessageRepository
from repositories.friendship_repository import FriendshipRepository
from core.redis_client import increment_unread, reset_unread
from schemas.message.message_read import MessageRead


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        friendship_repo: FriendshipRepository,
    ):
        self.message_repo = message_repo
        self.friendship_repo = friendship_repo

    async def _ensure_are_friends(self, user_id: int, other_user_id: int):
        are_friends = await self.friendship_repo.are_friends(user_id, other_user_id)
        if not are_friends:
            raise PermissionError("Users are not friends")

    async def send_message(
        self,
        *,
        sender_id: int,
        receiver_id: int,
        content: str,
    ) -> Message:
            try:
                await self._ensure_are_friends(sender_id, receiver_id)
                
                msg = await self.message_repo.create(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    content=content,
                )
                await increment_unread(receiver_id, sender_id)
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
        mark_read: bool = True,
    ) -> List[Message]:
            try:
                await self._ensure_are_friends(user_id, with_user_id)

                messages = await self.message_repo.get_conversation(
                    user_id=user_id,
                    with_user_id=with_user_id,
                    limit=limit,
                    before_id=before_id,
                )
                if mark_read:
                    updated = await self.message_repo.mark_messages_as_read(
                        receiver_id=user_id,
                        from_user_id=with_user_id,
                    )
                    if updated:
                        await reset_unread(user_id, with_user_id)

                        friendship = await self.friendship_repo.get_friendship_row(
                            user_id=user_id,
                            friend_id=with_user_id,
                        )

                        if friendship:
                            last_message = updated[-1]
                            friendship.last_read_message_id = last_message.id
                            friendship.unread_count = 0
                            await self.friendship_repo.commit()

                return messages
            except Exception as e:
                pass

    async def get_conversation_as_schema(
        self,
        *,
        user_id: int,
        with_user_id: int,
        limit: int = 100,
        before_id: Optional[int] = None,
    ) -> list[MessageRead]:
            try:
                messages = await self.message_repo.get_conversation(
                    user_id=user_id,
                    with_user_id=with_user_id,
                    limit=limit,
                    before_id=before_id,
                )
                return [MessageRead.model_validate(m) for m in messages]
            except Exception as e:
                pass
