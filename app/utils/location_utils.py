"""
Location utilities for event ingestion
"""
import json
from typing import List, Tuple

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.utils.cache_keys import USER_LOCATIONS_KEY, TTL_USER_LOCATIONS
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def get_unique_user_locations(redis=None) -> List[Tuple[str, str]]:
    """
    Get unique city/state combinations from user locations.
    Used for targeted event ingestion.

    Replaces Firestore full-collection stream of 2K users
    with a single SQL DISTINCT query on indexed columns.
    """
    if redis is not None:
        try:
            cached = await redis.get(USER_LOCATIONS_KEY)
            if cached:
                return [tuple(pair) for pair in json.loads(cached)]
        except Exception:
            pass

    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT DISTINCT city, state
            FROM users
            WHERE city IS NOT NULL AND city <> ''
              AND state IS NOT NULL AND state <> ''
        """))
        locations = [(row.city.strip(), row.state.strip()) for row in result.fetchall()]

    if redis is not None:
        try:
            await redis.set(USER_LOCATIONS_KEY, json.dumps(locations), ex=TTL_USER_LOCATIONS)
        except Exception:
            pass

    return locations
