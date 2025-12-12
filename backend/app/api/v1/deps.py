from functools import lru_cache
from typing import AsyncGenerator
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import session as session_module
from app.db.session import get_async_session
from app.core.config import get_settings
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.friend_request_repository import FriendRequestRepository
from app.repositories.friendship_repository import FriendshipRepository
from app.repositories.message_reaction_repository import MessageReactionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.services.conversation_service import ConversationService
from app.services.friend_request_service import FriendRequestService
from app.services.friendship_service import FriendshipService
from app.services.message_service import MessageService
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

@lru_cache(maxsize=2)
def _build_openai_client(api_key: str | None, base_url: str | None) -> AsyncOpenAI:
    kwargs = {}
    if base_url:
        kwargs["base_url"] = base_url
    if api_key:
        kwargs["api_key"] = api_key
    return AsyncOpenAI(**kwargs)

def get_openai_client() -> AsyncOpenAI | None:
    settings = get_settings()
    if settings.AI_PROVIDER.lower() == "ollama":
        return _build_openai_client(api_key="ollama", base_url=settings.OLLAMA_BASE_URL)
    if not settings.OPENAI_API_KEY:
        return None
    return _build_openai_client(api_key=settings.OPENAI_API_KEY, base_url=None)

def get_message_service(session: AsyncSession = Depends(get_async_session)) -> MessageService:
    repo = MessageRepository(session)
    conversation_repo = ConversationRepository(session)
    user_repo = UserRepository(session)
    reaction_repo = MessageReactionRepository(session)
    settings = get_settings()
    openai_client = get_openai_client()
    return MessageService(
        repo,
        conversation_repo,
        user_repo,
        reaction_repo,
        openai_client,
        model_name=settings.AI_MODEL,
    )

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
