import logging

from app.db.base import Base
from app.db.session import async_engine

logger = logging.getLogger(__name__)


def _import_models() -> None:
    """
    Import all models so SQLAlchemy metadata is populated before create_all.
    """
    import app.models.conversation  # noqa: F401
    import app.models.conversation_member  # noqa: F401
    import app.models.friend_request  # noqa: F401
    import app.models.friendship  # noqa: F401
    import app.models.message  # noqa: F401
    import app.models.user  # noqa: F401


async def init_db() -> None:
    """
    Ensure database tables exist for the current engine.
    """
    _import_models()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema ensured")
