import pytest

import app.core.redis_client as rc
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_message_create_and_query(session_factory):
    async with session_factory() as db_session:
        user_repo = UserRepository(db_session)
        conv_repo = ConversationRepository(db_session)
        msg_repo = MessageRepository(db_session)

        u1 = await user_repo.create("test_provider", "provider_id_x", "sender@test", "username_sender", None)
        u2 = await user_repo.create("test_provider", "provider_id_y", "other@test", "username_other", None)

        conv = await conv_repo.get_or_create_dm(u1.id, u2.id)

        msg = await msg_repo.create(conversation_id=conv.id, sender_id=u1.id, content="hello world")

        fetched = await msg_repo.get_by_id(msg.id)
        assert fetched is not None
        assert fetched.content == "hello world"

        msgs = await msg_repo.get_messages(conversation_id=conv.id)
        assert any(m.id == msg.id for m in msgs)

@pytest.mark.asyncio
async def test_message_pagination_and_ordering(session_factory):
    async with session_factory() as db_session:
        user_repo = UserRepository(db_session)
        conv_repo = ConversationRepository(db_session)
        msg_repo = MessageRepository(db_session)

        a = await user_repo.create("test", "pa@test", "pa@test", "pa", None)
        b = await user_repo.create("test", "pb@test", "pb@test", "pb", None)

        conv = await conv_repo.get_or_create_dm(a.id, b.id)

        # create 120 messages
        for i in range(120):
            sender = a.id if (i % 2 == 0) else b.id
            await msg_repo.create(conversation_id=conv.id, sender_id=sender, content=f"msg-{i}")

        # fetch latest 50 (default)
        page1 = await msg_repo.get_messages(conversation_id=conv.id, limit=50)
        assert len(page1) == 50
        # ensure order is ascending chronological for UI (repo reverses)
        assert page1[0].created_at <= page1[-1].created_at

        # pagination by before_id: get older messages before the first id of page1
        before_id = page1[0].id
        page2 = await msg_repo.get_messages(conversation_id=conv.id, limit=50, before_id=before_id)
        assert len(page2) == 50
        assert page2[-1].created_at <= page1[0].created_at

@pytest.mark.asyncio
async def test_mark_messages_as_read_resets_unread_and_flags(session_factory, monkeypatch):
    async with session_factory() as db_session:
        user_repo = UserRepository(db_session)
        conv_repo = ConversationRepository(db_session)
        msg_repo = MessageRepository(db_session)

        a = await user_repo.create("test", "r1@test", "r1@test", "r1", None)
        b = await user_repo.create("test", "r2@test", "r2@test", "r2", None)

        conv = await conv_repo.get_or_create_dm(a.id, b.id)

        await msg_repo.create(conversation_id=conv.id, sender_id=b.id, content="hello")
        await msg_repo.create(conversation_id=conv.id, sender_id=b.id, content="hello 2")

        async def fake_reset_unread(user_id, conv_id):
            return None
        monkeypatch.setattr(rc, "reset_unread", fake_reset_unread)

        unread = await msg_repo.mark_messages_as_read(conversation_id=conv.id, user_id=a.id)
        assert all(m.read for m in unread)