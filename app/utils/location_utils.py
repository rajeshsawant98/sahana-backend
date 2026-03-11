"""
Location utilities for event ingestion
"""
import json
from app.auth.firebase_init import get_firestore_client
from app.utils.logger import get_logger
from app.utils.cache_keys import USER_LOCATIONS_KEY, TTL_USER_LOCATIONS
from typing import List, Tuple

logger = get_logger(__name__)


async def get_unique_user_locations(redis=None) -> List[Tuple[str, str]]:
    """
    Get unique city/state combinations from user locations in Firestore.
    Used for targeted event ingestion.

    Returns:
        List of (city, state) tuples from user profiles
    """
    if redis is not None:
        try:
            cached = await redis.get(USER_LOCATIONS_KEY)
            if cached:
                return [tuple(pair) for pair in json.loads(cached)]
        except Exception:
            pass

    db = get_firestore_client()
    users_ref = db.collection("users")
    users = users_ref.stream()

    cities = set()
    async for user in users:
        data = user.to_dict()
        loc = data.get("location", {})
        if not isinstance(loc, dict):
            logger.debug(f"Unexpected location type: {type(loc)} value: {loc}")
        city = loc.get("city") if isinstance(loc, dict) else None
        state = loc.get("state") if isinstance(loc, dict) else None
        if city and state:
            cities.add((city.strip(), state.strip()))

    result = list(cities)

    if redis is not None:
        try:
            await redis.set(USER_LOCATIONS_KEY, json.dumps(result), ex=TTL_USER_LOCATIONS)
        except Exception:
            pass

    return result
