from datetime import datetime
from typing import Dict
from uuid import uuid4

def ticketmaster_to_sahana_format(event: Dict) -> Dict:
    venue = event.get("_embedded", {}).get("venues", [{}])[0]

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

    categories = set()
    for item in event.get("classifications", []):
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
        "imageUrl": event.get("images", [{}])[0].get("url"),
        "createdBy": "Ticketmaster",
        "createdByEmail": "scraper@ticketmaster.com",
        "createdAt": datetime.utcnow().isoformat(),
        "description": event.get("info") or event.get("pleaseNote") or "No description available",
        "rsvpList": [],
        "origin": "external",
        "source": "ticketmaster",
        "originalId": event.get("id"),
    }


# Eventbrite parser
def eventbrite_to_sahana_format(event: Dict) -> Dict:
    return {
        "eventId": str(uuid4()),
        "eventName": event.get("title", "Untitled Event").strip(),
        "location": {
            "name": "Eventbrite Event",
            "city": "Tempe",
            "state": "AZ",
            "country": "United States",
            "latitude": None,
            "longitude": None,
            "formattedAddress": "N/A"
        },
        "startTime": None,
        "duration": 120,
        "categories": ["General"],
        "isOnline": False,
        "joinLink": event.get("link"),
        "imageUrl": None,
        "createdBy": "Eventbrite",
        "createdByEmail": "scraper@eventbrite.com",
        "createdAt": datetime.utcnow().isoformat(),
        "description": event.get("date", "No description available"),
        "rsvpList": [],
        "origin": "external",
        "source": "eventbrite",
        "originalId": event.get("link")
    }

