from typing import List, Optional
from fastapi import HTTPException

from app.repositories.conversation_repository import ConversationRepository
from app.repositories.user_repository import UserRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.conversation.conversation_read import ConversationRead
from app.schemas.message.message_read import MessageRead
from app.models.conversation import Conversation
from app.models.message import Message

from uuid import UUID
from app.schemas.conversation.conversation_preview import ConversationPreview
from app.schemas.user.user_read import UserRead

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

    async def get_user_conversation_previews(self, user_id: UUID) -> List[ConversationPreview]:
        """
        Main method for: 'list all conversations of a user'
        """
        conversations = await self.conversation_repo.get_user_conversations(user_id)
        conversation_ids = [c.id for c in conversations]
        last_messages = await self.conversation_repo.get_last_messages_for_conversations(conversation_ids)

        previews: List[ConversationPreview] = []

        for conv in conversations:
            last_msg = last_messages.get(conv.id)

            # Membership row for THIS user (for unread_count)
            my_member = next(
                (m for m in conv.members if m.user_id == user_id),
                None,
            )
            unread_count = my_member.unread_count if my_member else 0

            # Other users for DMs
            other_users = [
                UserRead.model_validate(m.user)
                for m in conv.members
                if m.user_id != user_id and m.user is not None
            ]

            previews.append(
                ConversationPreview(
                    id=conv.id,
                    is_group=conv.is_group,
                    name=conv.name,
                    last_message=last_msg.content if last_msg else None,
                    last_message_at=last_msg.created_at if last_msg else None,
                    unread_count=unread_count,
                    other_users=other_users,
                )
            )

        # Sort by last message time (most recent first)
        previews.sort(
            key=lambda p: (p.last_message_at is not None, p.last_message_at),
            reverse=True,
        )

        return previews


    async def get_or_create_dm(self, user_a_id, user_b_id) -> Conversation:
        if user_a_id == user_b_id:
            raise HTTPException(400, "Cannot create DM with yourself")

        # Confirm both users exist
        if not await self.user_repo.get_by_id(user_b_id):
            raise HTTPException(404, "User not found")

        return await self.conversation_repo.get_or_create_dm(user_a_id, user_b_id)


    async def create_group(self, creator_id: str, name: str, member_ids: List[str]) -> Conversation:
        if not name:
            raise HTTPException(400, "Group name is required")

        # Validate all members exist
        for uid in member_ids:
            if not await self.user_repo.get_by_id(uid):
                raise HTTPException(404, f"User {uid} not found")

        conversation = await self.conversation_repo.create_group(name, creator_id)

        # Add invited members
        for uid in member_ids:
            await self.conversation_repo.add_member(conversation.id, uid)

        return conversation

    async def add_member(self, conversation_id, user_id):
        conv = await self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise HTTPException(404, "Conversation not found")
        
        if not conv.is_group:
            raise HTTPException(400, "Cannot add members to a direct chat")

        await self.conversation_repo.add_member(conversation_id, user_id)

    async def remove_member(self, conversation_id, user_id):
        conv = await self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise HTTPException(404, "Conversation not found")

        if not conv.is_group:
            raise HTTPException(400, "Cannot remove members from a direct chat")

        await self.conversation_repo.remove_member(conversation_id, user_id)

    async def get_user_conversations(self, user_id: str) -> List[Conversation]:
        return await self.conversation_repo.get_user_conversations(user_id)

    async def send_message(self, conversation_id, sender_id, content: str) -> Message:
        conv = await self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise HTTPException(404, "Conversation not found")
        
        if not await self.conversation_repo.is_member(conversation_id, sender_id):
            raise HTTPException(403, "You are not part of this conversation")

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
            raise HTTPException(404, "Conversation not found")
        
        if not await self.conversation_repo.is_member(conversation_id, user_id):
            raise HTTPException(403, "You are not part of this conversation")

        messages = await self.message_repo.get_messages(
            conversation_id=conversation_id,
            limit=limit,
            before_id=before_id,
        )

        # Mark as read
        if mark_read and messages:
            last_msg = messages[-1]
            await self.conversation_repo.update_last_read(
                conversation_id=conversation_id,
                user_id=user_id,
                message_id=last_msg.id
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
            raise HTTPException(404, "Conversation not found")
        
        if not await self.conversation_repo.is_member(conversation_id, user_id):
            raise HTTPException(403, "You are not part of this conversation")

        return ConversationRead.model_validate(conv)
