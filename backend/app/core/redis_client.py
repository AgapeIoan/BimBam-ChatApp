from redis import asyncio as redis
from typing import List, Dict
from core.config import get_settings
from redis.exceptions import RedisError
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,  
)


def k_online_users() -> str:
    return "presence:online_users"

def k_user_online(user_id) -> str:
    return f"presence:user:{user_id}:online"

def k_user_typing(conversation_id, user_id) -> str:
    return f"typing:conv:{conversation_id}:user:{user_id}"

def k_unread(conversation_id, user_id) -> str:
    return f"unread:conv:{conversation_id}:user:{user_id}"

async def set_user_online(user_id, ttl: int = 60):
    try:
        pipe = redis_client.pipeline()
        pipe.sadd(k_online_users(), str(user_id))
        pipe.set(k_user_online(user_id), "1", ex=ttl)
        await pipe.execute()
    except RedisError as e:
        logger.error(f"Redis error in set_user_online: {e}")

async def set_user_offline(user_id):
    try:
        pipe = redis_client.pipeline()
        pipe.srem(k_online_users(), str(user_id))
        pipe.delete(k_user_online(user_id))
        await pipe.execute()
    except RedisError as e:
        logger.error(f"Redis error in set_user_offline: {e}")

async def get_online_users() -> List[str]:
    try:
        users = await redis_client.smembers(k_online_users())
        return list(users)
    except RedisError as e:
        logger.error(f"Redis error in get_online_users: {e}")
        return []


async def is_online(user_id) -> bool:
    try:
        return await redis_client.exists(k_user_online(user_id)) == 1
    except RedisError as e:
        logger.error(f"Redis error in is_online: {e}")
        return False

async def set_typing(conversation_id, user_id, ttl: int = 5):
    """
    Mark a user as typing in a specific conversation.
    Auto-expires quickly.
    """
    try:
        await redis_client.set(k_user_typing(conversation_id, user_id), "1", ex=ttl)
    except RedisError as e:
        logger.error(f"Redis error in set_typing: {e}")


async def clear_typing(conversation_id, user_id):
    try:
        await redis_client.delete(k_user_typing(conversation_id, user_id))
    except RedisError as e:
        logger.error(f"Redis error in clear_typing: {e}")


async def is_typing(conversation_id, user_id) -> bool:
    try:
        return await redis_client.exists(k_user_typing(conversation_id, user_id)) == 1
    except RedisError as e:
        logger.error(f"Redis error in is_typing: {e}")
        return False

async def increment_unread(conversation_id, user_id, amount: int = 1):
    """
    Increase the unread count for this conversation for this user.
    Key: unread:conv:<conversation_id>:user:<user_id>
    """
    try:
        key = k_unread(conversation_id, user_id)
        await redis_client.incrby(key, amount)
    except RedisError as e:
        logger.error(f"Redis error in increment_unread: {e}")


async def reset_unread(user_id, conversation_id):
    """
    Reset unread count to zero for this conversation for this user.
    """
    try:
        key = k_unread(conversation_id, user_id)
        await redis_client.set(key, 0)
    except RedisError as e:
        logger.error(f"Redis error in reset_unread: {e}")


async def get_unread(conversation_id, user_id) -> int:
    """
    Return unread count for a specific conversation.
    """
    try:
        key = k_unread(conversation_id, user_id)
        value = await redis_client.get(key)
        return int(value or 0)
    except RedisError as e:
        logger.error(f"Redis error in get_unread: {e}")
        return 0

async def get_all_unread_for_user(user_id) -> Dict[str, int]:
    unread_map = {}
    try:
        pattern = f"unread:conv:*:user:{user_id}"

        async for key in redis_client.scan_iter(pattern):
            conv_id = key.split(":")[2]
            unread_count = await redis_client.get(key)
            unread_map[conv_id] = int(unread_count or 0)
            
    except RedisError as e:
        logger.error(f"Redis error in get_all_unread_for_user: {e}")
        return {}

    return unread_map
