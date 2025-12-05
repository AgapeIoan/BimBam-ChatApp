from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.v1.deps import get_db
from backend.app.models.user import User
from backend.app.models.conversation import Conversation
from backend.app.models.conversation_member import ConversationMember
from backend.app.models.message import Message

router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("/seed")
async def seed_demo_data(db: AsyncSession = Depends(get_db)):
    """
    TEMP: Seed demo data for testing conversations.

    Creates:
    - 2 users
    - 1 conversation between them
    - 3 messages
    """

    # 1) Users  (remove id=uuid4() if your model autogenerates)
    user1 = User(
        id=uuid4(),
        email="alice@example.com",
        username="alice",
        provider="debug",
        provider_id="alice-debug",
        avatar_url=None,
    )
    user2 = User(
        id=uuid4(),
        email="bob@example.com",
        username="bob",
        provider="debug",
        provider_id="bob-debug",
        avatar_url=None,
    )

    db.add_all([user1, user2])
    await db.flush()

    # 2) One DM conversation
    conv = Conversation(is_group=False, name=None)
    db.add(conv)
    await db.flush()

    # 3) Members
    member1 = ConversationMember(
        conversation_id=conv.id,
        user_id=user1.id,
        is_admin=False,
        unread_count=0,
    )
    member2 = ConversationMember(
        conversation_id=conv.id,
        user_id=user2.id,
        is_admin=False,
        unread_count=2,
    )
    db.add_all([member1, member2])
    await db.flush()

    # 4) Messages
    msg1 = Message(
        conversation_id=conv.id,
        sender_id=user1.id,
        content="Hey Bob! This is our first message.",
        delivered=True,
        read=False,
    )
    msg2 = Message(
        conversation_id=conv.id,
        sender_id=user1.id,
        content="Are you coming to the meeting?",
        delivered=True,
        read=False,
    )
    msg3 = Message(
        conversation_id=conv.id,
        sender_id=user2.id,
        content="Yes, I’ll be there!",
        delivered=True,
        read=True,
    )
    db.add_all([msg1, msg2, msg3])

    await db.commit()
    await db.refresh(user1)
    await db.refresh(user2)
    await db.refresh(conv)

    return {
        "message": "Seeded demo data.",
        "user1_id": str(user1.id),
        "user2_id": str(user2.id),
        "conversation_id": str(conv.id),
    }
