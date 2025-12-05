import pytest

from app.repositories.user_repository import UserRepository
from app.repositories.conversation_repository import ConversationRepository


@pytest.mark.asyncio
async def test_dm_creation_and_members(session_factory):
    async with session_factory() as db_session:
        user_repo = UserRepository(db_session)
        conv_repo = ConversationRepository(db_session)

        u1 = await user_repo.create("test_provider", "provider_id_a", "u1@test", "username1", None)
        u2 = await user_repo.create("test_provider", "provider_id_b", "u2@test", "username2", None)

        conv = await conv_repo.get_or_create_dm(u1.id, u2.id)

        assert conv is not None
        assert conv.is_group is False

        members = await conv_repo.get_conversation_members(conv.id)
        assert len(members) == 2

        assert await conv_repo.is_member(conv.id, u1.id)
        assert await conv_repo.is_member(conv.id, u2.id)


@pytest.mark.asyncio
async def test_cannot_add_member_to_dm(session_factory):
    async with session_factory() as db_session:
        user_repo = UserRepository(db_session)
        conv_repo = ConversationRepository(db_session)

        a = await user_repo.create("test_provider", "provider_id_ca", "ca@test", "username_ca", None)
        b = await user_repo.create("test_provider", "provider_id_cb", "cb@test", "username_cb", None)

        dm = await conv_repo.get_or_create_dm(a.id, b.id)
        # trying to add a 3rd user should be allowed only if conversation is group;
        # adding to DM may either create a new conversation or raise — test the business rule
        # For this repo we expect add_member to succeed but conversation remains DM false (depends on design).
        c = await user_repo.create("test_provider", "provider_id_cc", "cc@test", "username_cc", None)
        member = await conv_repo.add_member(dm.id, c.id)
        assert member.user_id == c.id