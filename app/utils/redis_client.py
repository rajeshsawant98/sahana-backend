import os
from typing import Any, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

_redis_client = None


async def init_redis() -> None:
    global _redis_client
    url = os.getenv("REDIS_URL")
    if not url:
        logger.warning("REDIS_URL not set — Redis disabled, falling back to file cache / Firestore dedup")
        return
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=False,
            max_connections=5,
        )
        await client.ping()
        _redis_client = client
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis unavailable ({e}) — continuing without Redis")
        _redis_client = None


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed")


def get_redis_client() -> Optional[Any]:
    return _redis_client
