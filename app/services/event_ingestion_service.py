import os
import requests
from typing import List
from app.repositories.event_ingestion_repository import EventIngestionRepository
from app.auth.firebase_init import get_firestore_client
from app.utils.event_parser import ticketmaster_to_sahana_format
from app.services.event_scraping_service import get_eventbrite_events
from app.utils.cache_utils import load_url_cache, save_url_cache

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
        "size": 20,
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

    return [ticketmaster_to_sahana_format(ev) for ev in data["_embedded"]["events"]]

# --- Location Utility ---

def get_unique_user_locations() -> list[tuple[str, str]]:
    db = get_firestore_client()
    users_ref = db.collection("users")
    users = users_ref.stream()

    cities = set()
    for user in users:
        data = user.to_dict()
        loc = data.get("location", {})
        city = loc.get("city")
        state = loc.get("state")
        if city and state:
            cities.add((city.strip(), state.strip()))
    return list(cities)

# --- Ingestion Logic ---

def ingest_event(event: dict) -> bool:
    original_id = event.get("originalId")
    if not original_id:
        return repo.save_event(event)

    existing = repo.get_by_original_id(original_id)
    if existing:
        print(f"[SKIP] Event with originalId={original_id} already exists.")
        return False

    return repo.save_event(event)

def ingest_bulk_events(events: list[dict]) -> dict:
    total = len(events)
    saved = skipped = 0

    for e in events:
        if ingest_event(e):
            saved += 1
        else:
            skipped += 1

    return {
        "total": total,
        "saved": saved,
        "skipped": skipped
    }

async def ingest_events_for_all_cities() -> dict:
    from app.services.event_ingestion_service import get_unique_user_locations  # keep here to avoid circular import

    total_events = 0
    summary = []
    url_cache = load_url_cache()

    for city, state in get_unique_user_locations():
        events = []

        # 1. Fetch from Ticketmaster (sync)
        try:
            tm_events = fetch_ticketmaster_events(city, state)
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
        result = ingest_bulk_events(events)
        total_events += result["saved"]
        summary.append(f"{result['saved']} new events for {city}, {state}")
        
    save_url_cache(url_cache)

    return {
        "total_events": total_events,
        "processed_cities": len(summary),
        "summary": summary
    }