from typing import AsyncGenerator
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import session as session_module
from app.db.session import get_async_session
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.friend_request_repository import FriendRequestRepository
from app.repositories.friendship_repository import FriendshipRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.services.conversation_service import ConversationService
from app.services.friend_request_service import FriendRequestService
from app.services.friendship_service import FriendshipService
from app.services.user_service import UserService
from app.utils.jwt_utils import decode_access_token


async def get_current_user(
    acces_token: str = Cookie(default=None, alias="access_token"),
    session: AsyncSession = Depends(get_async_session),
):
    if not acces_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    payload = decode_access_token(acces_token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    try:
        user_id = UUID(str(payload["sub"]))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        )

    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user


def get_user_service(session: AsyncSession = Depends(get_async_session)) -> UserService:
    repo = UserRepository(session)
    return UserService(repo)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session without wrapping it in an implicit transaction block.
    """
    async with session_module.AsyncSessionLocal() as session:
        yield session


def get_conversation_service(
    session: AsyncSession = Depends(get_async_session),
) -> ConversationService:
    conv_repo = ConversationRepository(session)
    user_repo = UserRepository(session)
    message_repo = MessageRepository(session)
    return ConversationService(conv_repo, user_repo, message_repo)


def get_friend_request_service(
    session: AsyncSession = Depends(get_async_session),
) -> FriendRequestService:
    friend_request_repo = FriendRequestRepository(session)
    user_repo = UserRepository(session)
    friendship_repo = FriendshipRepository(session)
    return FriendRequestService(user_repo, friendship_repo, friend_request_repo)

def get_friendship_service(session: AsyncSession = Depends(get_async_session)) -> FriendshipService:
    friendship_repo = FriendshipRepository(session)
    user_repo = UserRepository(session)
    return FriendshipService(friendship_repo, user_repo)
