import os
import json
import requests
import asyncio
from typing import List
from app.repositories.events import EventIngestionRepository
from app.utils.event_parser import ticketmaster_to_sahana_format
from app.services.event_scraping_service import get_eventbrite_events
from app.utils.cache_utils import load_url_cache, save_url_cache
from app.utils.location_utils import get_unique_user_locations
from app.utils.logger import get_service_logger
from app.utils.redis_client import get_redis_client
from app.utils.cache_keys import (
    INGESTED_IDS_KEY, TTL_INGESTED_IDS,
    INGESTION_LOCK_KEY, TTL_INGESTION_LOCK,
    tm_cache_key, TTL_TM_API,
)
# imported lazily to avoid circular import
def _flush_event_query_cache():
    from app.services.event_service import flush_event_query_cache
    return flush_event_query_cache()

logger = get_service_logger(__name__)

# Repo is used for all DB operations
repo = EventIngestionRepository()

# --- Ticketmaster Fetcher ---

def fetch_ticketmaster_events(city: str, state: str) -> List[dict]:
    api_key = os.getenv("TICKETMASTER_API_KEY")
    if not api_key:
        raise ValueError("Missing TICKETMASTER_API_KEY in environment")

    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": api_key,
        "city": city,
        "stateCode": state,
        "countryCode": "US",
        "size": 30,
        "sort": "date,asc"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Ticketmaster API error: {e}")
        return []

    data = response.json()
    if "_embedded" not in data:
        return []

    # Only include events with a valid startTime
    formatted = [ticketmaster_to_sahana_format(ev) for ev in data["_embedded"]["events"]]
    filtered = [ev for ev in formatted if ev.get("startTime")]
    return filtered


# --- Ingestion Logic ---

async def ingest_event(event: dict, redis=None) -> bool:
    original_id = event.get("originalId")
    if not original_id:
        return await repo.save_event(event)

    # Fast dedup via Redis SET
    if redis is not None:
        try:
            if await redis.sismember(INGESTED_IDS_KEY, original_id):
                logger.debug(f"[Redis] Event originalId={original_id} already ingested, skipping.")
                return False
        except Exception:
            pass

    existing = await repo.get_by_original_id(original_id)
    if existing:
        logger.debug(f"Event with originalId={original_id} already exists, skipping.")
        return False

    saved = await repo.save_event(event)

    if saved and redis is not None:
        try:
            await redis.sadd(INGESTED_IDS_KEY, original_id)
            await redis.expire(INGESTED_IDS_KEY, TTL_INGESTED_IDS)
        except Exception:
            pass

    return saved


async def ingest_bulk_events(events: list[dict], redis=None) -> dict:
    total = len(events)
    saved = skipped = 0

    for e in events:
        if await ingest_event(e, redis=redis):
            saved += 1
        else:
            skipped += 1

    return {
        "total": total,
        "saved": saved,
        "skipped": skipped
    }

# ── Ticketmaster pipeline (serialized — 1 request/s to avoid 429) ────────────

async def _fetch_tm_all_cities(locations: list[tuple[str, str]], redis=None) -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {}
    for city, state in locations:
        key = f"{city},{state}"
        cache_key = tm_cache_key(city, state)

        # Check Redis cache first
        if redis is not None:
            try:
                cached = await redis.get(cache_key)
                if cached:
                    results[key] = json.loads(cached)
                    logger.info(f"[TM][cache] {city}, {state}: {len(results[key])} events")
                    continue
            except Exception:
                pass

        try:
            events = await asyncio.to_thread(fetch_ticketmaster_events, city, state)
            results[key] = events
            logger.info(f"[TM] {city}, {state}: {len(events)} events")

            if redis is not None:
                try:
                    await redis.set(cache_key, json.dumps(events), ex=TTL_TM_API)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"[TM] {city}, {state} failed: {e}")
            results[key] = []

        await asyncio.sleep(1)  # rate limit only on cache miss

    return results


# ── Eventbrite pipeline (3 concurrent browsers) ───────────────────────────────

_eb_semaphore = asyncio.Semaphore(3)


async def _fetch_eb_city(city: str, state: str, url_cache: set) -> tuple[str, list[dict]]:
    key = f"{city},{state}"
    async with _eb_semaphore:
        try:
            events = await get_eventbrite_events(city, state, seen_links=url_cache)
            logger.info(f"[EB] {city}, {state}: {len(events)} events")
            return key, events
        except Exception as e:
            logger.error(f"[EB] {city}, {state} failed: {e}")
            return key, []


# ── Ticketmaster-only orchestrator (used by Cloud Run Job / run_ingestion.py) ─

async def ingest_ticketmaster_events_for_all_cities() -> dict:
    """
    Ingests only Ticketmaster events — no browser/Playwright required.
    Called by the daily Cloud Run Job via run_ingestion.py.
    """
    redis = get_redis_client()

    if redis is not None:
        try:
            lock_acquired = await redis.set(INGESTION_LOCK_KEY, "1", nx=True, ex=TTL_INGESTION_LOCK)
            if not lock_acquired:
                logger.warning("TM ingestion already running (lock held), skipping.")
                return {"status": "skipped", "reason": "ingestion_locked"}
        except Exception as e:
            logger.warning(f"Could not acquire ingestion lock ({e}), proceeding without lock")
            redis = None

    try:
        locations = await get_unique_user_locations(redis=redis)
        logger.info(f"[TM-only] Starting ingestion for {len(locations)} cities")

        tm_results = await _fetch_tm_all_cities(locations, redis=redis)

        summary = []
        for city, state in locations:
            key = f"{city},{state}"
            events = tm_results.get(key, [])
            result = await ingest_bulk_events(events, redis=redis) if events else {"saved": 0, "skipped": 0}
            summary.append({
                "location": f"{city}, {state}",
                "fetched": len(events),
                "saved": result["saved"],
                "skipped": result["skipped"],
            })

        try:
            await _flush_event_query_cache()
        except Exception as e:
            logger.warning(f"Could not flush event query cache post-ingestion: {e}")

        total_events = sum(r["saved"] for r in summary)
        return {
            "status": "success",
            "total_ingested": total_events,
            "processed_cities": len(summary),
            "details": summary,
        }
    finally:
        if redis is not None:
            try:
                await redis.delete(INGESTION_LOCK_KEY)
            except Exception:
                pass


# ── Full orchestrator (Ticketmaster + Eventbrite) ─────────────────────────────

async def ingest_events_for_all_cities() -> dict:
    redis = get_redis_client()

    # Mutex lock — prevent concurrent ingestion runs
    if redis is not None:
        try:
            lock_acquired = await redis.set(INGESTION_LOCK_KEY, "1", nx=True, ex=TTL_INGESTION_LOCK)
            if not lock_acquired:
                logger.warning("Ingestion already running (lock held), skipping.")
                return {"status": "skipped", "reason": "ingestion_locked"}
        except Exception as e:
            logger.warning(f"Could not acquire ingestion lock ({e}), proceeding without lock")
            redis = None  # disable Redis for this run if lock check failed

    try:
        url_cache = await load_url_cache(redis=redis)
        locations = await get_unique_user_locations(redis=redis)

        logger.info(f"Starting ingestion for {len(locations)} cities")

        # Phase 1 — Ticketmaster (sequential, rate-limit safe)
        logger.info("Phase 1: Ticketmaster")
        tm_results = await _fetch_tm_all_cities(locations, redis=redis)

        # Phase 2 — Eventbrite (parallel, browser-limited)
        logger.info("Phase 2: Eventbrite")
        eb_pairs = await asyncio.gather(*[_fetch_eb_city(c, s, url_cache) for c, s in locations])
        eb_results = dict(eb_pairs)

        # Phase 3 — Ingest merged results per city
        logger.info("Phase 3: Ingesting into Firestore")
        summary = []
        for city, state in locations:
            key = f"{city},{state}"
            events = tm_results.get(key, []) + eb_results.get(key, [])
            result = await ingest_bulk_events(events, redis=redis) if events else {"saved": 0, "skipped": 0}
            summary.append({
                "location": f"{city}, {state}",
                "fetched": len(events),
                "saved": result["saved"],
                "skipped": result["skipped"],
            })

        await save_url_cache(url_cache, redis=redis)

        # Invalidate event query cache so fresh data is served
        try:
            await _flush_event_query_cache()
        except Exception as e:
            logger.warning(f"Could not flush event query cache post-ingestion: {e}")

        total_events = sum(r["saved"] for r in summary)
        return {
            "status": "success",
            "total_ingested": total_events,
            "processed_cities": len(summary),
            "details": summary,
        }
    finally:
        if redis is not None:
            try:
                await redis.delete(INGESTION_LOCK_KEY)
            except Exception:
                pass
