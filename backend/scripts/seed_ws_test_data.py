"""
Quickly seed dev data so WebSocket tests can run against a fresh database.

Usage example:
python scripts/seed_ws_test_data.py --token <token_for_user_a> --token <token_for_user_b>
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Sequence
from uuid import UUID

import jwt

# Ensure project root (parent of scripts/) is on sys.path so `app` package is importable
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import Settings, get_settings  # noqa: E402
from app.db.init_db import init_db  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.repositories.conversation_repository import ConversationRepository  # noqa: E402
from app.repositories.user_repository import UserRepository  # noqa: E402


def _user_id_from_token(token: str, settings: Settings) -> UUID:
    payload = jwt.decode(token, settings.AUTH.JWT_SECRET, algorithms=[settings.AUTH.JWT_ALGORITHM])
    sub = payload.get("sub")
    if not sub:
        raise ValueError("Token missing subject (sub)")
    return UUID(str(sub))


async def seed(tokens: Sequence[str], skip_dm: bool, settings: Settings) -> None:
    await init_db()

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        users = []

        for token in tokens:
            try:
                user_id = _user_id_from_token(token, settings)
            except Exception as exc:  # noqa: BLE001
                print(f"Skipping token because it could not be decoded: {exc}")
                continue

            existing = await user_repo.get_by_id(user_id)
            if existing:
                print(f"User {user_id} already exists as {existing.email}")
                users.append(existing)
                continue

            username = f"user-{str(user_id)[:8]}"
            email = f"{username}@example.com"
            user = User(
                id=user_id,
                provider="dev",
                provider_id=str(user_id),
                email=email,
                username=username,
                avatar_url=None,
            )
            session.add(user)
            users.append(user)
            print(f"Created user {user_id} ({email})")

        await session.flush()

        conversation_id = None
        if not skip_dm and len(users) >= 2:
            conv_repo = ConversationRepository(session)
            convo = await conv_repo.get_or_create_dm(users[0].id, users[1].id)
            conversation_id = convo.id
            print(
                f"Ensured DM conversation between {users[0].id} and {users[1].id}: {conversation_id}"
            )

        await session.commit()

    if conversation_id:
        print(f"Use conversationId={conversation_id} for message_send tests")


def main():
    parser = argparse.ArgumentParser(description="Seed WebSocket test users into the database.")
    parser.add_argument(
        "--token",
        action="append",
        required=True,
        help="JWT token whose subject (sub) will be used as the user id. Pass multiple times for multiple users.",
    )
    parser.add_argument(
        "--skip-dm",
        action="store_true",
        help="Skip creating a DM conversation between the first two users.",
    )
    parser.add_argument(
        "--db-url",
        help="Override DATABASE__DB_URL for local runs (e.g. postgres+asyncpg://user:pass@localhost:5432/example_db).",
    )

    args = parser.parse_args()

    if args.db_url:
        os.environ["DATABASE__DB_URL"] = args.db_url

    settings = get_settings()
    print(f"Using DB URL: {settings.DATABASE.DB_URL}")
    asyncio.run(seed(args.token, args.skip_dm, settings))


if __name__ == "__main__":
    main()
