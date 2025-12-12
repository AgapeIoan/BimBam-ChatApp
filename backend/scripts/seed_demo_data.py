"""
Seed a realistic demo group chat scenario for presentations.

Usage:
  python scripts/seed_demo_data.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from sqlalchemy import delete, select

# Ensure project root is on sys.path so `app` package is importable
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.db.init_db import init_db  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.conversation import Conversation  # noqa: E402
from app.models.conversation_member import ConversationMember  # noqa: E402
from app.models.message import Message  # noqa: E402
from app.models.user import User  # noqa: E402


async def ensure_users(session) -> Dict[str, User]:
    """Ensure the four demo users exist and return them by key."""
    demo_users = [
        ("alex", "Alex Popescu", "alex.popescu@example.com"),
        ("maria", "Maria Ionescu", "maria.ionescu@example.com"),
        ("andrei", "Andrei Radu", "andrei.radu@example.com"),
        ("elena", "Elena Dan", "elena.dan@example.com"),
    ]

    existing_users = (
        await session.execute(select(User).where(User.email.in_([email for _, _, email in demo_users])))
    ).scalars()
    found_by_email = {u.email: u for u in existing_users}

    created: Dict[str, User] = {}
    for key, full_name, email in demo_users:
        if email in found_by_email:
            created[key] = found_by_email[email]
            continue
        avatar_url = f"https://i.pravatar.cc/150?u={key}"
        user = User(
            id=uuid4(),
            provider="demo",
            provider_id=email,
            email=email,
            username=full_name,
            avatar_url=avatar_url,
        )
        session.add(user)
        created[key] = user

    await session.flush()
    return created


async def purge_conversations(session):
    """Clear messages and conversations while keeping users."""
    await session.execute(delete(Message))
    await session.execute(delete(ConversationMember))
    await session.execute(delete(Conversation))
    await session.flush()


async def seed_demo():
    await init_db()
    async with AsyncSessionLocal() as session:
        try:
            await purge_conversations(session)
            users = await ensure_users(session)

            # Create group conversation
            convo = Conversation(
                id=uuid4(),
                is_group=True,
                name="Cabana Weekend 🌲",
            )
            session.add(convo)
            await session.flush()

            # Add members
            for user in users.values():
                session.add(
                    ConversationMember(
                        id=uuid4(),
                        conversation_id=convo.id,
                        user_id=user.id,
                        is_admin=False,
                    )
                )
            await session.flush()

            # Build timeline
            now = datetime.now(timezone.utc)
            start = now - timedelta(days=2)
            messages_plan: List[tuple[str, str, timedelta]] = [
                ("alex", "Salutare! Ce ziceti de o iesire la munte weekendul asta?", timedelta(minutes=0)),
                ("maria", "Daa! Chiar voiam sa propun.", timedelta(minutes=10)),
                ("andrei", "Depinde unde. Nu vreau sa conduc 5 ore.", timedelta(minutes=20)),
                ("elena", "Am gasit o cabana libera la Porumbacu.", timedelta(minutes=35)),
                ("alex", "Trimite link.", timedelta(minutes=37)),
                ("elena", "Uite aici boking.com/cabana-porumbacu.", timedelta(minutes=40)),
                ("maria", "Super!", timedelta(minutes=45)),
                ("maria", "E aproape de Sibiu, nu?", timedelta(minutes=46)),
                ("maria", "Cat e pretul pe noapte?", timedelta(minutes=47)),
                ("andrei", "Pretul e ok, dar sa nu fie drum prost.", timedelta(minutes=55)),
                ("alex", "Harta arata drum ok. Plecam sambata dimineata?", timedelta(minutes=65)),
                ("elena", "Da, eu pot de la 9.", timedelta(minutes=70)),
                ("andrei", "Mai bine 10, sa evitam traficul.", timedelta(minutes=75)),
                ("maria", "Pot la 10. Si luam mancare?", timedelta(minutes=80)),
                ("alex", "Fac eu lista de cumparaturi diseara.", timedelta(hours=8)),  # same day evening
                ("elena", "Noapte buna! Maine stabilim meniul.", timedelta(hours=12)),  # night gap
                ("andrei", "Dimineata buna, mergem pe Valea Oltului?", timedelta(hours=24)),  # next day morning
                ("maria", "Da, mai scurt.", timedelta(hours=24, minutes=30)),
                ("alex", "Ne vedem maine la 10 in parcarea de la Auchan.", timedelta(days=2) - timedelta(minutes=5)),
            ]

            base_time = start
            for sender_key, content, delta in messages_plan:
                created_at = base_time + delta
                session.add(
                    Message(
                        id=uuid4(),
                        conversation_id=convo.id,
                        sender_id=users[sender_key].id,
                        content=content,
                        created_at=created_at,
                        delivered=True,
                        read=False,
                    )
                )

            await session.commit()
            print("Database seeded successfully!")
        except Exception as exc:  # noqa: BLE001
            await session.rollback()
            raise exc


def main():
    # Allow overriding DB URL for local runs
    settings = get_settings()
    os.environ.setdefault("DATABASE__DB_URL", settings.DATABASE.DB_URL)
    asyncio.run(seed_demo())


if __name__ == "__main__":
    main()
