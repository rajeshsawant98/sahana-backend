import os
import requests
from typing import List
from app.repositories.event_ingestion_repository import EventIngestionRepository
from app.auth.firebase_init import get_firestore_client
from app.utils.event_parser import ticketmaster_to_sahana_format

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

def ingest_events_for_all_cities() -> dict:
    total_events = 0
    summary = []

    for city, state in get_unique_user_locations():
        events = fetch_ticketmaster_events(city, state)
        result = ingest_bulk_events(events)
        total_events += result["saved"]
        summary.append(f"{result['saved']} new events for {city}, {state}")

    return {
        "total_events": total_events,
        "processed_cities": len(summary),
        "details": summary
    }