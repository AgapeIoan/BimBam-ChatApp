from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from models.friendship import Friendship
from models.message import Message
from sqlalchemy import select
from repositories.message_repository import MessageRepository
from repositories.friendship_repository import FriendshipRepository
from core.redis_client import increment_unread, reset_unread
from schemas.message.message_read import MessageRead


class MessageService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def _ensure_are_friends(self, user_id: int, other_user_id: int) -> None:
        result = await self._session.execute(
            select(Friendship).where(
                Friendship.user_id == user_id,
                Friendship.friend_id == other_user_id,
            )
        )
        friendship = result.scalars().one_or_none()
        if not friendship:
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
                repo = MessageRepository(self._session)
                msg = await repo.create(
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
                repo = MessageRepository(self._session)
                messages = await repo.get_conversation(
                    user_id=user_id,
                    with_user_id=with_user_id,
                    limit=limit,
                    before_id=before_id,
                )
                if mark_read:
                    updated = await repo.mark_messages_as_read(
                        self,
                        receiver_id=user_id,
                        from_user_id=with_user_id,
                    )
                    if updated:
                        await reset_unread(user_id, with_user_id)

                    friendship_repo = FriendshipRepository(self._session)
                    are_friends = await friendship_repo.are_friends(user_id, with_user_id)
                    if are_friends and updated:
                        result = await self._session.execute(
                            select(Friendship).where(
                                Friendship.user_id == user_id,
                                Friendship.friend_id == with_user_id,
                            )
                        )
                        friendship = result.scalars().one_or_none()
                        if friendship:
                            last = updated[-1]
                            friendship.last_read_message_id = last.id
                            friendship.unread_count = 0
                            await self._session.commit()
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
                messages = await self.get_conversation(
                    user_id=user_id,
                    with_user_id=with_user_id,
                    limit=limit,
                    before_id=before_id,
                )
                return [MessageRead.model_validate(m) for m in messages]
            except Exception as e:
                pass
