import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from uuid import uuid4
from typing import Dict, List
from app.db.firestore_client import save_event_to_firestore
from app.auth.firebase_config import get_firestore_client

load_dotenv()  # Load .env variables

def ticketmaster_to_sahana_format(event: Dict) -> Dict:
    venue = event.get("_embedded", {}).get("venues", [{}])[0]

    # Coordinates
    lat = venue.get("location", {}).get("latitude")
    lng = venue.get("location", {}).get("longitude")

    location = {
        "name": venue.get("name", "Unknown Venue").strip(),
        "city": venue.get("city", {}).get("name", "Unknown"),
        "state": venue.get("state", {}).get("stateCode", "AZ"),
        "country": venue.get("country", {}).get("name", "United States"),
        "latitude": float(lat) if lat else None,
        "longitude": float(lng) if lng else None,
        "formattedAddress": venue.get("address", {}).get("line1", "N/A")
    }

    # Category tags
    categories = set()
    if event.get("classifications"):
        for item in event["classifications"]:
            segment = item.get("segment", {}).get("name")
            genre = item.get("genre", {}).get("name")
            sub_genre = item.get("subGenre", {}).get("name")

            if segment and segment != "Undefined":
                categories.add(segment)
            if genre and genre != "Undefined":
                categories.add(genre)
            if sub_genre and sub_genre != "Undefined":
                categories.add(sub_genre)

    if not categories:
        categories = {"General"}

    is_online = "online" in location["name"].lower()

    return {
        "eventId": event.get("id") or str(uuid4()),
        "eventName": event.get("name", "Untitled Event").strip(),
        "location": location,
        "startTime": event.get("dates", {}).get("start", {}).get("dateTime"),
        "duration": 120,
        "categories": list(categories),
        "isOnline": is_online,
        "joinLink": event.get("url"),
        "imageURL": event.get("images", [{}])[0].get("url"),
        "createdBy": "Ticketmaster",
        "createdByEmail": "scraper@ticketmaster.com",
        "createdAt": datetime.utcnow().isoformat(),
        "description": event.get("info") or event.get("pleaseNote") or "No description available",
        "rsvpList": []
    }


def fetch_ticketmaster_events(city: str, state: str) -> List[Dict]:
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
        print(f"[ERROR] Failed to fetch from Ticketmaster API: {e}")
        return []

    data = response.json()
    if "_embedded" not in data:
        print("[INFO] No events found.")
        return []

    raw_events = data["_embedded"]["events"]
    events = []

    for event in raw_events:
        try:
            cleaned = ticketmaster_to_sahana_format(event)
            save_event_to_firestore(cleaned)
            events.append(cleaned)
        except Exception as e:
            print(f"[WARN] Skipping event due to error: {e}")

    print(f"[INFO] Retrieved and saved {len(events)} events for {city}, {state}")
    return events


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


def ingest_events_for_all_cities() -> dict:
    locations = get_unique_user_locations()
    total_events = 0
    summary = []

    for city, state in locations:
        events = fetch_ticketmaster_events(city, state)
        total_events += len(events)
        summary.append(f"{len(events)} events for {city}, {state}")

    return {
        "total_events": total_events,
        "processed_cities": len(locations),
        "details": summary
    }

# Fetch events from Firestore This function retrieves events from Firestore based on the city and state provided.
# It queries the "ticketmasterEvents" collection, filters by city and state, and returns a list of events.
def get_ticketmaster_events(city: str, state: str) -> list[dict]:
    db = get_firestore_client()
    print(f"📥 Querying for city: {city}, state: {state}")
    
    ref = db.collection("ticketmasterEvents")
    query = (
        ref.where("location.city", "==", city)
           .where("location.state", "==", state)
           .order_by("startTime")
           .limit(30)
    )
    
    events = [doc.to_dict() for doc in query.stream()]
    print(f"📤 Found {len(events)} events")
    return events