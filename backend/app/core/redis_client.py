import redis.asyncio as redis
from typing import List, Dict

from core.config import get_settings

settings = get_settings()


redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


# Keys
def k_online_users():
    return "online_users"

def k_user_online(uid: int):
    return f"user:{uid}:online"

def k_typing(uid: int, to_uid: int):
    return f"user:{uid}:typing:{to_uid}"

def k_unread(uid: int):
    return f"unread:{uid}"


# Presence
async def set_user_online(uid: int, ttl: int = 60):
    pipe = redis_client.pipeline()
    pipe.sadd(k_online_users(), uid)
    pipe.set(k_user_online(uid), "1", ex=ttl)
    await pipe.execute()


async def set_user_offline(uid: int):
    pipe = redis_client.pipeline()
    pipe.srem(k_online_users(), uid)
    pipe.delete(k_user_online(uid))
    await pipe.execute()


async def is_online(uid: int) -> bool:
    return await redis_client.exists(k_user_online(uid)) == 1


async def get_online_users() -> List[int]:
    result = await redis_client.smembers(k_online_users())
    return [int(x) for x in result]


# Typing
async def set_typing(uid: int, to_uid: int, ttl: int = 5):
    await redis_client.set(k_typing(uid, to_uid), "1", ex=ttl)


async def clear_typing(uid: int, to_uid: int):
    await redis_client.delete(k_typing(uid, to_uid))


async def is_typing(uid: int, to_uid: int) -> bool:
    return await redis_client.exists(k_typing(uid, to_uid)) == 1


# Unread
async def increment_unread(receiver_id: int, sender_id: int):
    await redis_client.hincrby(k_unread(receiver_id), sender_id, 1)


async def reset_unread(receiver_id: int, sender_id: int):
    await redis_client.hset(k_unread(receiver_id), sender_id, 0)


async def get_unread_map(uid: int) -> Dict[int, int]:
    result = await redis_client.hgetall(k_unread(uid))
    return {int(k): int(v) for k, v in result.items()}
