from typing import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker  # adjust if path differs

from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.services.conversation_service import ConversationService
from app.models.user import User


# 1) DB session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# 2) ConversationService dependency
def get_conversation_service(
    db: AsyncSession = Depends(get_db),
) -> ConversationService:
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    user_repo = UserRepository(db)

    return ConversationService(
        conversation_repo=conversation_repo,
        user_repo=user_repo,
        message_repo=message_repo,
    )


# 3) TEMPORARY current user dependency
async def get_current_user(
    user_id: UUID = Query(..., description="TEMP: user id until auth is implemented"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Temporary implementation:
    - takes user_id from query ?user_id=...
    - loads the user from DB
    Later, when auth exists, you'll replace this with logic that
    extracts the user from JWT / session / OAuth etc.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
