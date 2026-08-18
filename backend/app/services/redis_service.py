import redis
from app.core.config import settings
from app.core.logging import logger


def get_redis_client() -> redis.Redis:
    """
    Returns a configured Redis client instance using REDIS_URL.
    """
    return redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=3
    )


def check_redis_connection() -> bool:
    """
    Verifies Redis reachability by issuing a PING command.
    """
    try:
        client = get_redis_client()
        return client.ping()
    except Exception as e:
        logger.warning(f"Redis connection check failed: {e}")
        return False
