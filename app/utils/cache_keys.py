import hashlib
import json

# TTLs (seconds)
TTL_URL_CACHE = 30 * 24 * 3600       # 30 days
TTL_INGESTED_IDS = 30 * 24 * 3600    # 30 days
TTL_INGESTION_LOCK = 3600            # 1 hour
TTL_TM_API = 8 * 3600                # 8 hours
TTL_EVENT_QUERY = 600                # 10 minutes
TTL_USER_LOCATIONS = 1800            # 30 minutes

# Static keys
URL_CACHE_KEY = "sahana:url_cache"
INGESTED_IDS_KEY = "sahana:ingested_ids"
INGESTION_LOCK_KEY = "sahana:ingestion:lock"
USER_LOCATIONS_KEY = "sahana:user_locations"


def _slug(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def tm_cache_key(city: str, state: str) -> str:
    return f"sahana:tm:{_slug(city)}:{_slug(state)}"


def event_query_cache_key(cursor_params: dict, filters: dict) -> str:
    payload = json.dumps({"cursor": cursor_params, "filters": filters}, sort_keys=True)
    digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"sahana:events:q:{digest}"


def nearby_events_cache_key(city: str, state: str, cursor_params: dict) -> str:
    payload = json.dumps({"city": _slug(city), "state": _slug(state), "cursor": cursor_params}, sort_keys=True)
    digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"sahana:events:nearby:{digest}"
