import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from uuid import uuid4
from typing import Dict, List
from app.db.firestore_client import save_event_to_firestore

load_dotenv()  # Load .env variables

def ticketmaster_to_sahana_format(event: Dict) -> Dict:
    venue = event.get("_embedded", {}).get("venues", [{}])[0]

    # Coordinates
    lat = venue.get("location", {}).get("latitude")
    lng = venue.get("location", {}).get("longitude")

    location = {
        "name": venue.get("name", "Unknown Venue").strip(),
        "city": venue.get("city", {}).get("name", "Unknown"),
        "country": venue.get("country", {}).get("name", "United States"),
        "latitude": float(lat) if lat else None,
        "longitude": float(lng) if lng else None,
        "formattedAddress": venue.get("address", {}).get("line1", "N/A")
    }

    # Category tags
    categories = []
    if event.get("classifications"):
        for item in event["classifications"]:
            print(item)
            genre = item.get("genre", {}).get("name")
            segment = item.get("segment", {}).get("name")
            sub_genre = item.get("subGenre", {}).get("name")
            if segment and segment!= "Undefined": categories.append(segment)
            if genre and genre!= "Undefined": categories.append(genre)
            if sub_genre and sub_genre!= "Undefined": categories.append(sub_genre)  


    if not categories:
        categories = ["General"]

    # Determine online
    is_online = "online" in location["name"].lower()

    return {
        "eventId": event.get("id") or str(uuid4()),
        "eventName": event.get("name", "Untitled Event").strip(),
        "location": location,
        "startTime": event.get("dates", {}).get("start", {}).get("dateTime"),
        "duration": 120,
        "categories": list(set(categories)),
        "isOnline": is_online,
        "joinLink": event.get("url", None),
        "imageURL": event.get("images", [{}])[0].get("url", None),
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

    print(f"[INFO] Retrieved and sanitized {len(events)} events from Ticketmaster")
    return events