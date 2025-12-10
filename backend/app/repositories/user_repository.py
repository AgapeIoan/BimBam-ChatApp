from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalars().one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalars().one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.username == username)
        )
        return result.scalars().one_or_none()

    async def get_by_provider_id(self, provider: str, provider_id: str) -> User | None:
        result = await self._session.execute(
            select(User)
            .where(User.provider == provider)
            .where(User.provider_id == provider_id)
        )

        return result.scalars().one_or_none()

    async def create(
        self,
        provider: str,
        provider_id: str,
        email: str,
        username: str,
        avatar_url: str | None,
    ) -> User:
        user = User(
            provider=provider,
            provider_id=provider_id,
            email=email,
            username=username,
            avatar_url=avatar_url,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def update_last_seen(self, user_id: UUID):
        result = await self._session.execute(select(User).where(User.id == user_id))
        user = result.scalars().one()
        user.last_seen = datetime.now(timezone.utc)
        await self._session.flush()
        return user

    async def update_username(self, user: User, new_username: str) -> User:
        user.username = new_username
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def search_by_email(self, email_query: str) -> list[User]:
        result = await self._session.execute(
            select(User).where(User.email.ilike(f"%{email_query}%"))
        )
        return result.scalars().all()

    async def search_by_username(self, username_query: str) -> list[User]:
        result = await self._session.execute(
            select(User).where(User.username.ilike(f"%{username_query}%"))
        )
        return result.scalars().all()
