from typing import AsyncGenerator

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import models  # noqa: F401 to register models with Base
from app.core.config import get_settings

settings = get_settings()

db_url = make_url(settings.DATABASE.DB_URL)
connect_args: dict = {}

# Ensure full Unicode (emoji) support, especially for MySQL
if db_url.drivername.startswith("mysql"):
    query = dict(db_url.query)
    if query.get("charset", "").lower() != "utf8mb4":
        query["charset"] = "utf8mb4"
    db_url = db_url.set(query=query)
# For Postgres, enforce UTF8 client encoding (defaults to UTF8, but explicit is safe)
elif db_url.drivername.startswith("postgresql"):
    connect_args["server_settings"] = {"client_encoding": "UTF8"}

async_engine = create_async_engine(
    db_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session
