import os
import requests
import asyncio
from typing import List
from app.repositories.events import EventIngestionRepository
from app.auth.firebase_init import get_firestore_client
from app.utils.event_parser import ticketmaster_to_sahana_format
from app.services.event_scraping_service import get_eventbrite_events
from app.utils.cache_utils import load_url_cache, save_url_cache
from app.utils.location_utils import get_unique_user_locations

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
        print(f"[ERROR] Ticketmaster API error: {e}")
        return []

    data = response.json()
    if "_embedded" not in data:
        return []

    # Only include events with a valid startTime
    formatted = [ticketmaster_to_sahana_format(ev) for ev in data["_embedded"]["events"]]
    filtered = [ev for ev in formatted if ev.get("startTime")]
    return filtered


# --- Ingestion Logic ---

async def ingest_event(event: dict) -> bool:
    original_id = event.get("originalId")
    if not original_id:
        return await repo.save_event(event)

    existing = await repo.get_by_original_id(original_id)
    if existing:
        print(f"[SKIP] Event with originalId={original_id} already exists.")
        return False

    return await repo.save_event(event)

async def ingest_bulk_events(events: list[dict]) -> dict:
    total = len(events)
    saved = skipped = 0

    for e in events:
        if await ingest_event(e):
            saved += 1
        else:
            skipped += 1

    return {
        "total": total,
        "saved": saved,
        "skipped": skipped
    }

async def ingest_events_for_all_cities() -> dict:
    total_events = 0
    summary = []
    url_cache = load_url_cache()

    for city, state in get_unique_user_locations():
        events = []

        # 1. Fetch from Ticketmaster (sync, run in thread)
        try:
            tm_events = await asyncio.to_thread(fetch_ticketmaster_events, city, state)
            events.extend(tm_events)
        except Exception as e:
            print(f"[ERROR] Ticketmaster fetch failed for {city}, {state}: {e}")

        # 2. Fetch from Eventbrite (async)
        try:
            eb_events = await get_eventbrite_events(city, state, seen_links=url_cache)
            events.extend(eb_events)
        except Exception as e:
            print(f"[ERROR] Eventbrite scraping failed for {city}, {state}: {e}")

        # 3. Ingest into Firestore (with deduplication)
        if events:
            result = await ingest_bulk_events(events)
            summary.append({
                "location": f"{city}, {state}",
                "fetched": len(events),
                "saved": result["saved"],
                "skipped": result["skipped"]
            })
            total_events += result["saved"]
            
    save_url_cache(url_cache)
    return {"total_ingested": total_events, "details": summary}
    

async def ingest_ticketmaster_events_for_all_cities() -> dict:
    total_events = 0
    summary = []

    for city, state in get_unique_user_locations():
        events = []

        # 1. Fetch from Ticketmaster (sync)
        try:
            tm_events = fetch_ticketmaster_events(city, state)
            events.extend(tm_events)
        except Exception as e:
            print(f"[ERROR] Ticketmaster fetch failed for {city}, {state}: {e}")


        # 3. Ingest into Firestore (with deduplication)
        result = await ingest_bulk_events(events)
        total_events += result["saved"]
        summary.append(f"{result['saved']} new events for {city}, {state}")

    return {
        "total_events": total_events,
        "processed_cities": len(summary),
        "summary": summary
    }