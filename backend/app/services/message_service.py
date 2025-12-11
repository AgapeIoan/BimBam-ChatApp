from typing import List, Optional
from uuid import UUID

from app.core.redis_client import reset_unread
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_reaction_repository import MessageReactionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.message.message_page import MessagePage
from app.schemas.message.message_read import MessageRead
from app.utils.errors.database_exception import DatabaseException
from app.utils.errors.resource_not_found import ResourceNotFoundException
from app.utils.errors.unauthorized_exception import UnauthorizedException
from app.utils.errors.validation_exception import ValidationException


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        conversation_repo: ConversationRepository,
        user_repo: UserRepository,
        reaction_repo: MessageReactionRepository,
    ):
        self.message_repo = message_repo
        self.conversation_repo = conversation_repo
        self.user_repo = user_repo
        self.reaction_repo = reaction_repo

    async def _ensure_conversation_exists(self, conversation_id: UUID):
        conv = await self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise ResourceNotFoundException("Conversation not found")
        return conv

    async def _ensure_member(self, conversation_id: UUID, user_id: UUID):
        conv = await self._ensure_conversation_exists(conversation_id)

        is_member = await self.conversation_repo.is_member(conversation_id, user_id)
        if not is_member:
            raise UnauthorizedException("You are not part of this conversation.")
        return conv

    async def send_message(
        self,
        *,
        conversation_id: UUID,
        sender_id: UUID,
        content: str,
    ):
        if not content or not content.strip():
            raise ValidationException("Message content cannot be empty")

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

    async def mark_delivered(self, message_id: UUID):
        return await self.message_repo.mark_delivered(message_id)

    async def mark_read(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        before_message_id: Optional[UUID] = None,
    ):
        await self._ensure_member(conversation_id, user_id)
        updated = await self.message_repo.mark_messages_as_read(
            conversation_id=conversation_id,
            user_id=user_id,
            before_message_id=before_message_id,
        )

        if updated:
            await reset_unread(user_id, conversation_id)
            last_msg = updated[-1]
            await self.conversation_repo.update_last_read(
                conversation_id=conversation_id,
                user_id=user_id,
                message_id=last_msg.id,
            )

        return updated

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
        counts = await self.reaction_repo.get_counts_for_messages([m.id for m in messages])
        return [
            MessageRead.model_validate(m).model_copy(update={"reactions": counts.get(m.id, {})})
            for m in messages
        ]

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
        counts = await self.reaction_repo.get_counts_for_messages([m.id for m in messages])

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
            messages=[
                MessageRead.model_validate(m).model_copy(update={"reactions": counts.get(m.id, {})})
                for m in messages
            ],
            has_more=has_more,
            next_before_id=next_before_id,
        )
    
    async def edit_message(self, message_id: UUID, editor_id: UUID, new_content: str):

        if new_content is None:
            raise ValidationException("New content required")

        msg = await self.message_repo.get_by_id(message_id)
        if not msg:
            raise ResourceNotFoundException("Message not found")
        if msg.sender_id != editor_id:
            raise UnauthorizedException("Only the sender can edit the message")

        await self._ensure_member(msg.conversation_id, editor_id)

        updated_msg, edit_record = await self.message_repo.edit_message(message_id, editor_id, new_content)
        if not updated_msg:
            raise DatabaseException("Failed to edit message")
        return updated_msg, edit_record

    async def delete_message(self, message_id: UUID, requester_id: UUID):
        msg = await self.message_repo.get_by_id(message_id)
        if not msg:
            raise ResourceNotFoundException("Message not found")

        # allow only sender to delete for now
        if msg.sender_id != requester_id:
            raise UnauthorizedException("Only the sender can delete the message")
        await self._ensure_member(msg.conversation_id, requester_id)

        deleted = await self.message_repo.delete_message(message_id)
        return deleted

    async def add_reaction(self, message_id, user_id, emoji):
        msg = await self.message_repo.get_by_id(message_id)
        if not msg:
            raise ResourceNotFoundException("Message not found")
        
        if not emoji or not emoji.strip():
            raise ValidationException("Emoji cannot be empty")

        await self._ensure_member(msg.conversation_id, user_id)
        reaction = await self.reaction_repo.add_reaction(message_id, user_id, emoji)
        counts = await self.reaction_repo.get_reaction_counts(message_id)

        return reaction, counts

    async def remove_reaction(self, message_id, user_id, emoji):
        msg = await self.message_repo.get_by_id(message_id)
        if not msg:
            raise ResourceNotFoundException("Message not found")
        
        if not emoji or not emoji.strip():
            raise ValidationException("Emoji cannot be empty")

        removed = await self.reaction_repo.remove_reaction(message_id, user_id, emoji)
        counts = await self.reaction_repo.get_reaction_counts(message_id)
        return removed, counts

    async def get_reactions(self, message_id, user_id):
        msg = await self.message_repo.get_by_id(message_id)
        if not msg:
            raise ResourceNotFoundException("Message not found")

        await self._ensure_member(msg.conversation_id, user_id)

        reactions = await self.reaction_repo.get_reactions(message_id)
        return reactions

    async def get_reaction_users_for_emoji(self, message_id: UUID, user_id: UUID, emoji: str) -> List[str]:
        msg = await self.message_repo.get_by_id(message_id)
        if not msg:
            raise ResourceNotFoundException("Message not found")

        await self._ensure_member(msg.conversation_id, user_id)

        usernames_by_emoji = await self.reaction_repo.get_usernames_grouped_by_emoji(message_id)
        return usernames_by_emoji.get(emoji, [])
