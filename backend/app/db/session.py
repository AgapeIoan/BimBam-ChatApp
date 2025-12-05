from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from backend.app.core.config import get_settings  # ✅ use app., not backend.app

settings = get_settings()

async_engine = create_async_engine(
    settings.DATABASE.DB_URL,
    pool_pre_ping=True,
)

# session factory
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
)

async_session_maker = AsyncSessionLocal


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Optional helper if you ever want to inject directly.
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session
