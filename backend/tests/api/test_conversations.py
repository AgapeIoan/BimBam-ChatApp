from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.api.v1.deps import get_current_user
from app.main import app
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository


def test_list_conversations_returns_previews_sorted_by_last_message(
    event_loop, session_factory
):
    """
    Conversation list should include preview data and be ordered by last message time.
    """

    async def _seed():
        async with session_factory() as session:
            user_repo = UserRepository(session)
            conv_repo = ConversationRepository(session)
            msg_repo = MessageRepository(session)

            me = await user_repo.create(
                provider="test",
                provider_id="me",
                email="me@example.com",
                username="me",
                avatar_url=None,
            )
            alice = await user_repo.create(
                provider="test",
                provider_id="alice",
                email="alice@example.com",
                username="alice",
                avatar_url=None,
            )
            bob = await user_repo.create(
                provider="test",
                provider_id="bob",
                email="bob@example.com",
                username="bob",
                avatar_url=None,
            )

            # Older conversation with older last message
            old_conv = await conv_repo.create_conversation(is_group=False)
            await conv_repo.add_member(old_conv.id, me.id)
            await conv_repo.add_member(old_conv.id, alice.id)
            old_msg = await msg_repo.create(
                conversation_id=old_conv.id,
                sender_id=alice.id,
                content="old message",
            )
            old_msg.created_at = datetime.now(timezone.utc) - timedelta(minutes=5)

            # Newer conversation with newer last message and unread count
            new_conv = await conv_repo.create_conversation(is_group=False)
            my_membership = await conv_repo.add_member(new_conv.id, me.id)
            my_membership.unread_count = 3
            await conv_repo.add_member(new_conv.id, bob.id)
            new_msg = await msg_repo.create(
                conversation_id=new_conv.id,
                sender_id=bob.id,
                content="latest message",
            )

            await session.commit()
            return me, alice, bob, old_conv, new_conv, old_msg, new_msg

    me, alice, bob, old_conv, new_conv, old_msg, new_msg = event_loop.run_until_complete(
        _seed()
    )

    # Override auth to bypass JWT for the test client
    app.dependency_overrides[get_current_user] = lambda: me

    client = TestClient(app)
    response = client.get("/api/v1/conversations/")
    assert response.status_code == 200

    conversations = response.json()
    assert [c["id"] for c in conversations] == [str(new_conv.id), str(old_conv.id)]

    first = conversations[0]
    assert first["last_message"] == "latest message"
    assert first["last_message_at"] is not None
    assert first["unread_count"] == 3
    assert len(first["other_users"]) == 1
    assert first["other_users"][0]["id"] == str(bob.id)

    second = conversations[1]
    assert second["last_message"] == "old message"
    assert second["last_message_at"] is not None
    assert second["other_users"][0]["id"] == str(alice.id)

    first_ts = datetime.fromisoformat(first["last_message_at"])
    second_ts = datetime.fromisoformat(second["last_message_at"])
    assert first_ts > second_ts

    app.dependency_overrides.pop(get_current_user, None)
