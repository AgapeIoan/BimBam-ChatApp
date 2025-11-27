from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repository import UserRepository
from core.redis_client import set_user_online, set_user_offline


class UserService:

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_by_id(self, user_id: int):
        try:
            return await self.user_repo.get_by_id(user_id)
        except Exception as e:
            pass

    async def get_by_email(self, email: str):
        try:
            return await self.user_repo.get_by_email(email)
        except Exception as e:
            pass

    async def get_by_username(self, username: str):
        try:
            return await self.user_repo.get_by_username(username)
        except Exception as e:
            pass

    async def login_or_register(self, provider: str, provider_id: str, email: str, username: str, avatar_url: str | None):
        try:
            user = await self.user_repo.get_by_provider_id(provider, provider_id)
            if user:
                return user
            return await self.user_repo.create(provider, provider_id, email, username, avatar_url)
        except Exception as e:
            pass

    async def set_online(self, user_id: int):
        try:
            await set_user_online(user_id)
        except Exception as e:
            pass

    async def set_offline(self, user_id: int):
        try:
            await self.user_repo.update_last_seen(user_id)
            await set_user_offline(user_id)
        except Exception as e:
            pass
