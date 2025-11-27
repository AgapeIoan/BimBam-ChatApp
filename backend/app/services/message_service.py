from typing import List, Optional

from sqlalchemy.orm import Session

from models.friendship import Friendship
from models.message import Message
from repositories.message_repository import MessageRepository
from core.redis_client import increment_unread, reset_unread
from schemas.message import MessageRead


class MessageService:
    @staticmethod
    def _ensure_are_friends(db: Session, user_id: int, other_user_id: int) -> None:
    
        friendship = (
            db.query(Friendship)
            .filter(
                Friendship.user_id == user_id,
                Friendship.friend_id == other_user_id,
            )
            .one_or_none()
        )
        if not friendship:
            raise PermissionError("Users are not friends")

    @staticmethod
    async def send_message(
        db: Session,
        *,
        sender_id: int,
        receiver_id: int,
        body: str,
    ) -> Message:
        """
        Logic for sending a message:
        - check friendship
        - create message
        - increment unread count in Redis
        """
        MessageService._ensure_are_friends(db, sender_id, receiver_id)

        msg = MessageRepository.create(
            db,
            sender_id=sender_id,
            receiver_id=receiver_id,
            body=body,
        )

        await increment_unread(receiver_id, sender_id)

        return msg

    @staticmethod
    async def get_conversation(
        db: Session,
        *,
        user_id: int,
        with_user_id: int,
        limit: int = 100,
        before_id: Optional[int] = None,
        mark_read: bool = True,
    ) -> List[Message]:

        MessageService._ensure_are_friends(db, user_id, with_user_id)

        messages = MessageRepository.get_conversation(
            db,
            user_id=user_id,
            with_user_id=with_user_id,
            limit=limit,
            before_id=before_id,
        )


        if mark_read:
            updated = MessageRepository.mark_messages_as_read(
                db,
                receiver_id=user_id,
                from_user_id=with_user_id,
            )

            if updated:
                # Reset unread count in Redis
                await reset_unread(user_id, with_user_id)

                # sync basic unread info to Friendship row
                friendship = (
                    db.query(Friendship)
                    .filter(
                        Friendship.user_id == user_id,
                        Friendship.friend_id == with_user_id,
                    )
                    .one_or_none()
                )
                if friendship:
                    last = updated[-1]
                    friendship.last_read_message_id = last.id
                    friendship.unread_count = 0
                    db.commit()

        return messages

    @staticmethod
    async def get_conversation_as_schema(
        db: Session,
        *,
        user_id: int,
        with_user_id: int,
        limit: int = 100,
        before_id: Optional[int] = None,
    ) -> list[MessageRead]:

        messages = await MessageService.get_conversation(
            db,
            user_id=user_id,
            with_user_id=with_user_id,
            limit=limit,
            before_id=before_id,
        )
        return [MessageRead.model_validate(m) for m in messages]
