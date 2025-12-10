import asyncio
import os
from typing import Callable, Iterator, Optional

import pytest
from app.api.deps.websocket_auth import websocket_auth
from app.db import session as session_module
from app.db.base import Base
from app.main import app
from app.models.user import User
from app.websockets.connection_manager import connection_manager
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from tests.helpers import _init_fake_redis

# Ensure base env defaults for settings loading
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("DATABASE__DB_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
os.environ.setdefault("DATABASE__DB_HOST", "localhost")
os.environ.setdefault("DATABASE__DB_PORT", "5432")
os.environ.setdefault("DATABASE__DB_USER", "user")
os.environ.setdefault("DATABASE__DB_PASSWORD", "pass")
os.environ.setdefault("DATABASE__DB_NAME", "testdb")
os.environ.setdefault("SKIP_DB_INIT_ON_STARTUP", "1")


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def session_factory(event_loop) -> Iterator[async_sessionmaker[AsyncSession]]:
    async def _init():
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            future=True,
            echo=False,
            connect_args={"check_same_thread": False},
        )
        TestingSessionLocal = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Patch globals used by the app to point to the testing engine/session
        session_module.async_engine = engine
        session_module.AsyncSessionLocal = TestingSessionLocal
        # Ensure web socket event handlers also use the test sessionmaker
        import app.websockets.events as ws_events

        ws_events.AsyncSessionLocal = TestingSessionLocal

        # Import models so metadata is populated, then create schema
        import app.models.conversation  # noqa: F401
        import app.models.conversation_member  # noqa: F401
        import app.models.friend_request  # noqa: F401
        import app.models.friendship  # noqa: F401
        import app.models.message  # noqa: F401
        import app.models.user  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        return TestingSessionLocal, engine

    TestingSessionLocal, engine = event_loop.run_until_complete(_init())

    yield TestingSessionLocal

    event_loop.run_until_complete(engine.dispose())


@pytest.fixture(autouse=True)
def fake_redis():
    return _init_fake_redis()


@pytest.fixture(autouse=True)
def clear_connections():
    connection_manager._connections.clear()
    yield
    connection_manager._connections.clear()


@pytest.fixture(autouse=True)
def reset_db(event_loop, session_factory):
    async def _reset():
        async with session_module.async_engine.begin() as conn:
            await conn.exec_driver_sql("PRAGMA foreign_keys=OFF;")
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(text(f"DELETE FROM {table.name}"))
            await conn.exec_driver_sql("PRAGMA foreign_keys=ON;")
            await conn.commit()

    event_loop.run_until_complete(_reset())


@pytest.fixture
def user_factory(event_loop, session_factory) -> Callable[[str, str, Optional[str], Optional[str]], User]:
    """
    Synchronous factory to create a User in the test database.

    Usage in tests:
        user = user_factory("email@example.com", "username")
    """

    def _create_user(email: str, username: str, provider: Optional[str] = "test", provider_id: Optional[str] = None) -> User:
        async def _inner() -> User:
            async with session_module.AsyncSessionLocal() as session:
                assert isinstance(session, AsyncSession)
                user = User(
                    email=email,
                    username=username,
                    provider=provider or "test",
                    provider_id=provider_id or email,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user

        return event_loop.run_until_complete(_inner())

    return _create_user


@pytest.fixture
def conversation_factory(event_loop, session_factory):
    from app.repositories.conversation_repository import ConversationRepository

    def _create(user_ids):
        async def _create_async():
            async with session_factory() as session:
                repo = ConversationRepository(session)
                conv = await repo.create_conversation(is_group=False)
                for uid in user_ids:
                    await repo.add_member(conv.id, uid)
                await session.commit()
                return conv

        return event_loop.run_until_complete(_create_async())

    return _create


@pytest.fixture
def ws_auth_override():
    """
    Override websocket auth dependency to map simple tokens to created users.
    """

    token_user_map = {}

    from fastapi import WebSocket

    async def fake_auth(websocket: WebSocket):
        token = websocket.query_params.get("token")
        if not token or token not in token_user_map:
            from fastapi import status
            from fastapi.exceptions import WebSocketException

            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")

        return token_user_map[token]

    app.dependency_overrides[websocket_auth] = fake_auth
    yield token_user_map
    app.dependency_overrides.pop(websocket_auth, None)
