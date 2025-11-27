from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repository import UserRepository
from core.redis_client import set_user_online, set_user_offline


class UserService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: int):
        repo = UserRepository(self._session)
        return await repo.get_by_id(user_id)

    async def get_by_email(self, email: str):
        repo = UserRepository(self._session)
        return await repo.get_by_email(email)

    async def get_by_username(self, username: str):
        repo = UserRepository(self._session)
        return await repo.get_by_username(username)

    async def login_or_register(self, provider: str, provider_id: str, email: str, username: str, avatar_url: str | None):
        repo = UserRepository(self._session)
        user = await repo.get_by_provider_id(provider, provider_id)
        if user:
            return user
        return await repo.create(provider, provider_id, email, username, avatar_url)

    async def set_online(self, user_id: int):
        await set_user_online(user_id)

    async def set_offline(self, user_id: int):
        repo = UserRepository(self._session)
        await repo.update_last_seen(user_id)
        await set_user_offline(user_id)
