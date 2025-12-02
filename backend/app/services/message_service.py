from typing import List, Optional
from fastapi import HTTPException
from uuid import UUID

from repositories.message_repository import MessageRepository
from repositories.conversation_repository import ConversationRepository
from repositories.user_repository import UserRepository

from core.redis_client import increment_unread, reset_unread

from schemas.message.message_read import MessageRead
from schemas.message.message_page import MessagePage


class MessageService:

    def __init__(
        self,
        message_repo: MessageRepository,
        conversation_repo: ConversationRepository,
        user_repo: UserRepository,
    ):
        self.message_repo = message_repo
        self.conversation_repo = conversation_repo
        self.user_repo = user_repo

    async def _ensure_conversation_exists(self, conversation_id: UUID):
        conv = await self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise HTTPException(404, "Conversation not found")
        return conv

    async def _ensure_member(self, conversation_id: UUID, user_id: UUID):
        conv = await self._ensure_conversation_exists(conversation_id)

        is_member = await self.conversation_repo.is_member(conversation_id, user_id)
        if not is_member:
            raise HTTPException(status_code=403, detail="You are not part of this conversation.")
        return conv

    async def send_message(
        self,
        *,
        conversation_id: UUID,
        sender_id: UUID,
        content: str,
    ):

        if not content or not content.strip():
            raise HTTPException(400, "Message content cannot be empty")
        
        await self._ensure_member(conversation_id, sender_id)

        msg = await self.message_repo.create(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
        )

        await self.conversation_repo.increment_unread_for_others(
            conversation_id=conversation_id,
            sender_id=sender_id,
        )

        return msg


    async def get_messages(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        limit: int = 50,
        before_id: Optional[UUID] = None,
        mark_read: bool = True,
    ):

        await self._ensure_member(conversation_id, user_id)

        messages = await self.message_repo.get_messages(
            conversation_id=conversation_id,
            limit=limit,
            before_id=before_id,
        )

        # Mark as read
        if mark_read and messages:
            last_msg = messages[-1]
            updated = await self.message_repo.mark_messages_as_read(
                conversation_id=conversation_id,
                user_id=user_id,
                before_message_id=last_msg.id,
            )

            if updated:
                # Reset unread in Redis
                await reset_unread(user_id, conversation_id)

                # Sync DB unread indexes
                await self.conversation_repo.update_last_read(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    message_id=last_msg.id,
                )

        return messages


    async def get_messages_as_schema(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        limit: int = 50,
        before_id: Optional[UUID] = None,
    ) -> List[MessageRead]:

        messages = await self.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            before_id=before_id,
        )

        return [MessageRead.model_validate(m) for m in messages]

    # for infinite scroll UI
    async def get_message_page(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        limit: int = 50,
        before_id: Optional[UUID] = None,
    ) -> MessagePage:

        messages = await self.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            before_id=before_id,
        )

        if not messages:
            return MessagePage(
                conversation_id=conversation_id,
                messages=[],
                has_more=False,
                next_before_id=None,
            )

        # Determine if there are more messages
        oldest_msg = messages[0]

        # Try fetching one more older message
        extra = await self.message_repo.get_messages(
            conversation_id=conversation_id,
            limit=1,
            before_id=oldest_msg.id,
        )

        has_more = len(extra) > 0
        next_before_id = oldest_msg.id if has_more else None

        return MessagePage(
            conversation_id=conversation_id,
            messages=[MessageRead.model_validate(m) for m in messages],
            has_more=has_more,
            next_before_id=next_before_id,
        )
