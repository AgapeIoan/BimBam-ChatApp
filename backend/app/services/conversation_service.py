from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.conversation.conversation_preview import ConversationPreview
from app.schemas.conversation.conversation_read import ConversationRead
from app.schemas.message.message_read import MessageRead
from app.schemas.user.user_read import UserRead
from app.utils.errors.resource_not_found import ResourceNotFoundException
from app.utils.errors.unauthorized_exception import UnauthorizedException
from app.utils.errors.user_not_found_exception import UserNotFoundException
from app.utils.errors.validation_exception import ValidationException


class ConversationService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        user_repo: UserRepository,
        message_repo: MessageRepository,
    ):
        self.conversation_repo = conversation_repo
        self.user_repo = user_repo
        self.message_repo = message_repo

    async def get_or_create_dm(self, user_a_id, user_b_id) -> Conversation:
        if user_a_id == user_b_id:
            raise ValidationException("Cannot create DM with yourself")

        # Confirm both users exist
        if not await self.user_repo.get_by_id(user_b_id):
            raise UserNotFoundException("User not found")

        return await self.conversation_repo.get_or_create_dm(user_a_id, user_b_id)

    async def create_group(self, creator_id: UUID, name: str, participant_ids: List[UUID]) -> Conversation:
        if not name:
            raise ValidationException("Group name is required")

        # Deduplicate and exclude the creator
        participants = {uid for uid in participant_ids if uid != creator_id}

        if not participants:
            raise ValidationException("Add at least one member to the group")

        # Validate all members exist
        for uid in participants:
            if not await self.user_repo.get_by_id(uid):
                raise UserNotFoundException(f"User {uid} not found")

        conversation = await self.conversation_repo.create_group(name, creator_id)

        # Add invited members
        for uid in participants:
            await self.conversation_repo.add_member(conversation.id, uid)

        refreshed = await self.conversation_repo.get_by_id(conversation.id)
        return refreshed or conversation

    async def add_member(self, conversation_id, user_id):
        conv = await self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise ResourceNotFoundException("Conversation not found")

        if not conv.is_group:
            raise ValidationException("Cannot add members to a direct chat")

        await self.conversation_repo.add_member(conversation_id, user_id)

    async def remove_member(self, conversation_id, user_id):
        conv = await self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise ResourceNotFoundException("Conversation not found")

        if not conv.is_group:
            raise UnauthorizedException("Cannot remove members from a direct chat")

        await self.conversation_repo.remove_member(conversation_id, user_id)

    async def get_user_conversations(self, user_id: str) -> List[Conversation]:
        return await self.conversation_repo.get_user_conversations(user_id)

    async def get_user_conversation_previews(self, user_id: UUID) -> List[ConversationPreview]:
        conversations = await self.conversation_repo.get_user_conversations(user_id)
        conv_ids = [c.id for c in conversations]
        last_messages = await self.message_repo.get_latest_for_conversations(conv_ids)

        previews: list[tuple[datetime, ConversationPreview]] = []
        for conv in conversations:
            member_unread = 0
            for member in conv.members:
                if member.user_id == user_id:
                    member_unread = member.unread_count
                    break

            other_users = [
                UserRead.model_validate(m.user)
                for m in conv.members
                if m.user_id != user_id
            ]

            last_msg = last_messages.get(conv.id)
            sort_ts = last_msg["created_at"] if last_msg else conv.created_at

            previews.append(
                (
                    sort_ts,
                    ConversationPreview(
                        id=conv.id,
                        is_group=conv.is_group,
                        name=conv.name,
                        last_message=last_msg["content"] if last_msg else None,
                        last_message_at=last_msg["created_at"] if last_msg else None,
                        other_users=other_users,
                        unread_count=member_unread,
                    ),
                )
            )

        previews.sort(key=lambda item: item[0], reverse=True)
        return [p for _, p in previews]

    async def send_message(self, conversation_id, sender_id, content: str) -> Message:
        conv = await self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise ResourceNotFoundException("Conversation not found")

        if not await self.conversation_repo.is_member(conversation_id, sender_id):
            raise UnauthorizedException("You are not part of this conversation")

        message = await self.message_repo.create(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
        )

        await self.conversation_repo.increment_unread_for_others(
            conversation_id=conversation_id,
            sender_id=sender_id,
        )

        return message

    async def get_messages(
        self,
        conversation_id,
        user_id,
        limit: int = 50,
        before_id: Optional[str] = None,
        mark_read: bool = True,
    ) -> List[Message]:
        if not await self.conversation_repo.get_by_id(conversation_id):
            raise ResourceNotFoundException("Conversation not found")

        if not await self.conversation_repo.is_member(conversation_id, user_id):
            raise UnauthorizedException("You are not part of this conversation")

        messages = await self.message_repo.get_messages(
            conversation_id=conversation_id,
            limit=limit,
            before_id=before_id,
        )

        # Mark as read
        if mark_read and messages:
            last_msg = messages[-1]
            await self.conversation_repo.update_last_read(
                conversation_id=conversation_id, user_id=user_id, message_id=last_msg.id
            )

        return messages

    async def get_messages_as_schema(
        self,
        conversation_id,
        user_id,
        limit: int = 50,
        before_id: Optional[str] = None,
    ) -> List[MessageRead]:
        msgs = await self.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            before_id=before_id,
        )

        return [MessageRead.model_validate(m) for m in msgs]

    async def get_conversation_info(self, conversation_id, user_id):
        conv = await self.conversation_repo.get_by_id(conversation_id)

        if not conv:
            raise ResourceNotFoundException("Conversation not found")

        if not await self.conversation_repo.is_member(conversation_id, user_id):
            raise UnauthorizedException("You are not part of this conversation")

        return ConversationRead.model_validate(conv)
