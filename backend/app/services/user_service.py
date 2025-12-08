from uuid import UUID

from app.core.redis_client import set_user_offline, set_user_online
from app.repositories.user_repository import UserRepository


class UserService:

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_by_id(self, user_id: UUID):
        return await self.user_repo.get_by_id(user_id)

    async def get_by_email(self, email: str):
        return await self.user_repo.get_by_email(email)

    async def get_by_username(self, username: str):
        return await self.user_repo.get_by_username(username)

    async def login_or_register(self, provider: str, provider_id: str, email: str, username: str, avatar_url: str | None):
        user = await self.user_repo.get_by_provider_id(provider, provider_id)
        if user:
            return user
        return await self.user_repo.create(provider, provider_id, email, username, avatar_url)

    async def set_online(self, user_id: UUID):
        await set_user_online(user_id)

    async def set_offline(self, user_id: UUID):
        await self.user_repo.update_last_seen(user_id)
        await set_user_offline(user_id)
