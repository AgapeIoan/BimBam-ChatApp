from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError, DBAPIError

from models.conversation import Conversation
from models.conversation_member import ConversationMember


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_conversation(
        self,
        *,
        is_group: bool,
        name: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation (DM or Group)."""
        conv = Conversation(is_group=is_group, name=name)
        self.session.add(conv)
        try:
            await self.session.commit()
            await self.session.refresh(conv)
        except (IntegrityError, DBAPIError):
            await self.session.rollback()
            raise
        return conv

    async def get_by_id(self, conversation_id):
        """Fetch conversation with members + messages (lazy)."""
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.members))   # load members
        )
        return result.scalars().one_or_none()

    async def get_conversation_members(self, conversation_id) -> List[ConversationMember]:
        result = await self.session.execute(
            select(ConversationMember).where(ConversationMember.conversation_id == conversation_id)
        )
        return result.scalars().all()

    async def get_dm_conversation(self, user_a_id, user_b_id) -> Optional[Conversation]:
        """
        Returns an existing DM conversation between two users, if exists.
        """
        result = await self.session.execute(
            select(Conversation)
            .join(ConversationMember)
            .where(
                Conversation.is_group == False  
            )
            .group_by(Conversation.id)
            .having(
                func.count(ConversationMember.user_id) == 2
            )
        )

        conversations = result.scalars().all()

        for c in conversations:
            members = [m.user_id for m in c.members]
            if user_a_id in members and user_b_id in members:
                return c

        return None

    async def get_or_create_dm(self, user_a_id, user_b_id) -> Conversation:
        """
        Get a direct conversation between two users,
        or create a new one if it doesn't exist.
        """
        existing = await self.get_dm_conversation(user_a_id, user_b_id)
        if existing:
            return existing

        # Create new DM conversation
        conv = await self.create_conversation(is_group=False)

        # Add both members
        await self.add_member(conv.id, user_a_id)
        await self.add_member(conv.id, user_b_id)

        return conv

    async def create_group(self, name: str, creator_id) -> Conversation:
        """
        Create a named group conversation and add creator as admin.
        """
        conv = await self.create_conversation(is_group=True, name=name)
        await self.add_member(conv.id, creator_id, is_admin=True)
        return conv

    async def add_member(self, conversation_id, user_id, is_admin=False) -> ConversationMember:
        """
        Add one user to the conversation.
        """
        member = ConversationMember(
            conversation_id=conversation_id,
            user_id=user_id,
            is_admin=is_admin,
        )
        self.session.add(member)
        try:
            await self.session.commit()
            await self.session.refresh(member)
        except (IntegrityError, DBAPIError):
            await self.session.rollback()
            raise
        return member

    async def remove_member(self, conversation_id, user_id):
        """
        Remove member from conversation.
        """
        result = await self.session.execute(
            select(ConversationMember)
            .where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
            )
        )
        member = result.scalars().one_or_none()

        if not member:
            return None
        
        try:
            await self.session.delete(member)
            await self.session.commit()
        except (IntegrityError, DBAPIError):
            await self.session.rollback()
            raise

        return member

    async def is_member(self, conversation_id, user_id) -> bool:
        """
        Return True if user_id is part of conversation_id.
        """
        result = await self.session.execute(
            select(ConversationMember)
            .where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
            )
        )
        return result.scalars().one_or_none() is not None

    async def get_user_conversations(self, user_id) -> List[Conversation]:
        """
        Get all conversations (DM & group chats) a user is in.
        """
        result = await self.session.execute(
            select(Conversation)
            .join(ConversationMember)
            .where(ConversationMember.user_id == user_id)
            .options(selectinload(Conversation.members))
            .order_by(Conversation.created_at.desc())
        )
        return result.scalars().all()

    async def update_last_read(self, conversation_id, user_id, message_id):
        """
        Update last read message and reset unread count.
        """
        result = await self.session.execute(
            select(ConversationMember)
            .where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
            )
        )
        member = result.scalars().one_or_none()

        if not member:
            return None

        member.last_read_message_id = message_id
        member.unread_count = 0

        try:
            await self.session.commit()
        except (IntegrityError, DBAPIError):
            await self.session.rollback()
            raise
        return member

    async def increment_unread_for_others(self, conversation_id, sender_id):
        """
        Increase unread count for all members of a conversation except the sender.
        """
        members = await self.get_conversation_members(conversation_id)

        for m in members:
            if m.user_id != sender_id:
                m.unread_count += 1
    
        try:
            await self.session.commit()
        except (IntegrityError, DBAPIError):
            await self.session.rollback()
            raise

    async def commit(self):
        try:
            await self.session.commit()
        except (IntegrityError, DBAPIError):
            await self.session.rollback()
            raise