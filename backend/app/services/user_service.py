import re
from uuid import UUID

from app.core.redis_client import set_user_offline, set_user_online
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user.user_response import UserResponse
from app.utils.errors.validation_exception import ValidationException


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def _map_to_user_response(self, user: User):
        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            avatarUrl=user.avatar_url,
        )

    async def get_by_id(self, user_id: UUID):
        return await self.user_repo.get_by_id(user_id)

    async def get_by_email(self, email: str):
        return await self.user_repo.get_by_email(email)

    async def get_by_username(self, username: str):
        return await self.user_repo.get_by_username(username)

    async def login_or_register(
        self,
        provider: str,
        provider_id: str,
        email: str,
        username: str,
        avatar_url: str | None,
    ):
        user = await self.user_repo.get_by_provider_id(provider, provider_id)
        if not user:
            return await self.user_repo.create(
                provider=provider,
                provider_id=provider_id,
                email=email,
                username=username,
                avatar_url=avatar_url,
            )
        return user

    async def set_online(self, user_id: UUID):
        await set_user_online(user_id)

    async def set_offline(self, user_id: UUID):
        await self.user_repo.update_last_seen(user_id)
        await set_user_offline(user_id)

    async def update_username(self, user: User, new_username: str) -> str:
        new_username = new_username.strip()
        if len(new_username) < 3 or len(new_username) > 30:
            raise ValidationException("Username must be at least 3 characters long and alphanumeric")
        
        if not re.match("^[a-zA-Z0-9_]+$", new_username):
            raise ValidationException("Username must be alphanumeric and can contain underscores")
        
        existing_user = await self.user_repo.get_by_username(new_username)
        if existing_user and existing_user.id != user.id:
            raise ValidationException("Username is already taken")
        
        updated_user = await self.user_repo.update_username(user, new_username)
        return updated_user.username

    async def search_users_by_email(
        self, query: str, user_email: str
    ) -> list[UserResponse]:
        if not query:
            raise ValidationException("Email query cannot be empty")

        users = await self.user_repo.search_by_email(query, user_email)
        if not users:
            return []
        return [self._map_to_user_response(user) for user in users]

    async def search_users_by_username(
        self, query: str, user_email: str
    ) -> list[UserResponse]:
        if not query:
            raise ValidationException("Username query cannot be empty")
        users = await self.user_repo.search_by_username(query, user_email)
        if not users:
            return []
        return [self._map_to_user_response(user) for user in users]
