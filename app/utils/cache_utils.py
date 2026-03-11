import os
import json
from typing import Optional
from app.utils.cache_keys import URL_CACHE_KEY, TTL_URL_CACHE

# Detect Cloud Run for file fallback path
if os.getenv("K_SERVICE") or os.getenv("GOOGLE_CLOUD_PROJECT"):
    CACHE_FILE = "/tmp/seen_event_urls.json"
else:
    CACHE_FILE = "app/cache/seen_event_urls.json"


async def load_url_cache(redis=None) -> set:
    if redis is not None:
        try:
            members = await redis.smembers(URL_CACHE_KEY)
            return set(members)
        except Exception:
            pass
    # File fallback
    if not os.path.exists(CACHE_FILE):
        return set()
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except json.JSONDecodeError:
        return set()


async def save_url_cache(cache: set, redis=None) -> None:
    if redis is not None:
        try:
            if cache:
                await redis.sadd(URL_CACHE_KEY, *cache)
                await redis.expire(URL_CACHE_KEY, TTL_URL_CACHE)
            return
        except Exception:
            pass
    # File fallback
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(cache), f, indent=2)
