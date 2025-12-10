from typing import List
from uuid import UUID

from app.core.redis_client import get_online_users, is_online, set_user_offline, set_user_online


class PresenceService:
    """Presence management backed by Redis with optional TTL refresh."""

    def __init__(self, ttl_seconds: int = 60) -> None:
        self.ttl_seconds = ttl_seconds

    async def set_online(self, user_id: UUID) -> None:
        await set_user_online(user_id, ttl=self.ttl_seconds)

    async def set_offline(self, user_id: UUID) -> None:
        await set_user_offline(user_id)

    async def is_online(self, user_id: UUID) -> bool:
        return await is_online(user_id)

    async def get_online_users(self) -> List[str]:
        return await get_online_users()
