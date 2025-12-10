from typing import Optional

from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import redis_client
from app.main import app

from app.db import session as session_module
from app.main import app

from app.repositories.friendship_repository import FriendshipRepository
from app.models.user import User

try:
    import fakeredis.aioredis as _fakeredis_aioredis
except Exception:  # pragma: no cover - fallback used only in some test environments
    _fakeredis_aioredis = None


class _SimpleAsyncFakeRedis:
    """A tiny minimal async-compatible fake redis used as a fallback when
    `fakeredis` is not installed. Implements only the methods tests use.
    """

    def __init__(self):
        self._data = {}

    async def set(self, key, value, ex=None):
        self._data[key] = str(value)

    async def get(self, key):
        return self._data.get(key)

    async def exists(self, key):
        return 1 if key in self._data else 0

    async def smembers(self, key):
        val = self._data.get(key)
        if val is None:
            return set()
        return set(val) if isinstance(val, (set, list)) else {val}

    def pipeline(self):
        class _Pipe:
            def __init__(self, parent):
                self.parent = parent
                self.ops = []

            def sadd(self, key, val):
                self.ops.append(("sadd", key, val))

            def set(self, key, val, ex=None):
                self.ops.append(("set", key, val))

            def srem(self, key, val):
                self.ops.append(("srem", key, val))

            def delete(self, key):
                self.ops.append(("delete", key))

            async def execute(self):
                for op in self.ops:
                    if op[0] == "sadd":
                        k, v = op[1], op[2]
                        self.parent._data.setdefault(k, set()).add(v)
                    elif op[0] == "srem":
                        k, v = op[1], op[2]
                        if k in self.parent._data:
                            self.parent._data[k].discard(v)
                    elif op[0] == "set":
                        k, v = op[1], op[2]
                        self.parent._data[k] = str(v)
                    elif op[0] == "delete":
                        k = op[1]
                        self.parent._data.pop(k, None)

        return _Pipe(self)


def _init_fake_redis():
    if _fakeredis_aioredis is not None:
        fake = _fakeredis_aioredis.FakeRedis(decode_responses=True)
    else:
        fake = _SimpleAsyncFakeRedis()

    redis_client.redis_client = fake
    return fake

def _find_route_path(endpoint_name: str, method: Optional[str] = None) -> str:
    """
    Scan app.routes to find the path for an endpoint with the given function name.
    Optionally filter by HTTP method.
    """
    for route in app.routes:
        if isinstance(route, APIRoute) and route.endpoint.__name__ == endpoint_name:
            if method is None or method.upper() in route.methods:
                return route.path
    raise RuntimeError(f"Route for endpoint {endpoint_name!r} not found")

def _create_friendship_pair(user_a_id, user_b_id, event_loop):
    async def _inner():
        async with session_module.AsyncSessionLocal() as session:
            repo = FriendshipRepository(session)
            await repo.create_friendship_pair(user_a_id, user_b_id)
            await session.commit()

    event_loop.run_until_complete(_inner())

def _find_friend_conversation_route():
    """
    Find the path and HTTP method for the open_or_create_direct_conversation endpoint.
    We don't assume it's POST; we read what the router actually exposes.
    """
    for route in app.routes:
        if isinstance(route, APIRoute) and route.endpoint.__name__ == "open_or_create_direct_conversation":
            # Use any method other than HEAD/OPTIONS
            methods = [m for m in route.methods if m not in ("HEAD", "OPTIONS")]
            if not methods:
                raise RuntimeError("No valid HTTP method found for open_or_create_direct_conversation")
            return route.path, methods[0]
    raise RuntimeError("Route for open_or_create_direct_conversation not found")

async def _create_user(session: AsyncSession, email: str, username: str, provider: str = "google", provider_id: str | None = None) -> User:
    """
    Local helper to create a user with required OAuth fields populated.
    Avoids NOT NULL constraint issues on users.provider/users.provider_id.
    """
    if provider_id is None:
        provider_id = email  # something unique-ish and non-null

    user = User(
        email=email,
        username=username,
        provider=provider,
        provider_id=provider_id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user