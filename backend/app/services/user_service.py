from fastapi import HTTPException
import re
from uuid import UUID

from app.repositories.user_repository import UserRepository
from app.core.redis_client import set_user_online, set_user_offline
from app.models.user import User


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
        if not user:
            return await self.user_repo.create(provider = provider, provider_id=provider_id, email=email, username="", avatar_url=avatar_url)
        return user

    async def set_online(self, user_id: UUID):
        await set_user_online(user_id)

    async def set_offline(self, user_id: UUID):
        await self.user_repo.update_last_seen(user_id)
        await set_user_offline(user_id)

    async def update_username(self, user: User, new_username: str)-> str:
        new_username = new_username.strip()
        if len(new_username) < 3 or len(new_username) > 30:
            raise HTTPException(status_code=400, detail="Username must be at least 3 characters long and alphanumeric")
        
        if not re.match("^[a-zA-Z0-9_]+$", new_username):
            raise HTTPException(status_code=400, detail="Username must be alphanumeric and can contain underscores")
        
        existing_user = await self.user_repo.get_by_username(new_username)
        if existing_user and existing_user.id != user.id:
            raise HTTPException(status_code=400, detail="Username is already taken")
        
        updated_user = await self.user_repo.update_username(user, new_username)
        return updated_user.username
        
