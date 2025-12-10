import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_conversation_service
from app.db import session as session_module
from app.repositories.friendship_repository import FriendshipRepository
from app.repositories.user_repository import UserRepository
from app.services.conversation_service import ConversationService
from app.services.friendship_service import FriendshipService
from helpers import _create_user

@pytest.mark.asyncio
async def test_friendship_service_get_friends_integration():
    """
    Integration test:
    - Create two users
    - Create friendship pair
    - Use FriendshipService.get_friends() directly
    """
    async with session_module.AsyncSessionLocal() as session:
        assert isinstance(session, AsyncSession)

        me = await _create_user(session, "int-me@example.com", "int-me", provider="google", provider_id="int-me-google")
        friend = await _create_user(session, "int-friend@example.com", "int-friend", provider="google", provider_id="int-friend-google")

        friendship_repo = FriendshipRepository(session)
        user_repo = UserRepository(session)
        service = FriendshipService(friendship_repo, user_repo)

        await friendship_repo.create_friendship_pair(me.id, friend.id)
        await session.commit()

        friends = await service.get_friends(me.id)

    assert len(friends) == 1
    item = friends[0]
    assert item["friend"].id == friend.id
    assert item["unread_count"] == 0
    assert "is_online" in item


@pytest.mark.asyncio
async def test_conversation_service_get_or_create_dm_integration():
    """
    Integration:
    - Create users
    - Use ConversationService.get_or_create_dm()
    - Ensure it doesn't create duplicates.
    """
    async with session_module.AsyncSessionLocal() as session:
        assert isinstance(session, AsyncSession)

        me = await _create_user(session, "int-me2@example.com", "int-me2", provider="google", provider_id="int-me2-google")
        friend = await _create_user(session, "int-friend2@example.com", "int-friend2", provider="google", provider_id="int-friend2-google")
        conv_service = get_conversation_service(session=session) 

        conv1 = await conv_service.get_or_create_dm(me.id, friend.id)
        conv2 = await conv_service.get_or_create_dm(me.id, friend.id)

    assert conv1.id == conv2.id
    assert conv1.is_group is False
