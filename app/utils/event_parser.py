from datetime import datetime , timezone
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

    # Calculate duration from start and end times
    start_time = event.get("dates", {}).get("start", {}).get("dateTime")
    end_time = event.get("dates", {}).get("end", {}).get("dateTime")
    
    duration = 120  # Default duration in minutes
    if start_time and end_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration_seconds = (end_dt - start_dt).total_seconds()
            duration = int(duration_seconds // 60)  # Convert to minutes
        except (ValueError, TypeError):
            duration = 120  # Fallback to default if parsing fails

    return {
        "eventId": event.get("id") or str(uuid4()),
        "eventName": event.get("name", "Untitled Event").strip(),
        "location": location,
        "startTime": start_time,
        "duration": duration,
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
        # Archive/status fields
        "isArchived": False,
        "archivedAt": None,
        "archivedBy": None,
        "archiveReason": None,
    }

def safe_get_name(value):
    return value.get("name") if isinstance(value, dict) else str(value or "")

from typing import Optional

def parse_eventbrite_data(server_data: dict) -> Optional[dict]:
    """
    Parses Eventbrite server_data into Sahana event format.
    Returns None if event is missing start date or has abnormal duration (> 20160 min).
    """


    event = server_data.get("event", {})
    components = server_data.get("components", {})

    try:
        city = components.get("eventDetails", {}).get("location", {}).get("venueMultilineAddress", [None, "Unknown, XX"])[1].split(",")[0].strip()
    except Exception:
        city = "Unknown"
    state = event.get("venue", {}).get("region", "XX")

    image_url = server_data.get("event_listing_response", {}).get("schemaInfo", {}).get("schemaImageUrl", None)
    organizer_name = components.get("organizer", {}).get("name", "Eventbrite Organizer")

    event_map = components.get("eventMap", {})
    location = {
        "name": event_map.get("venueName", "Unknown Venue"),
        "city": city,
        "state": state,
        "country": "United States",
        "latitude": float(event_map.get("location", {}).get("latitude", 0.0)),
        "longitude": float(event_map.get("location", {}).get("longitude", 0.0)),
        "formattedAddress": event_map.get("venueAddress", "N/A")
    }

    tags = [
        tag.get("text")
        for tag in components.get("tags", [])
        if isinstance(tag, dict) and "text" in tag
    ]

    description = components.get("eventDescription", {}).get("summary", "")
    join_link = components.get("eventDetails", {}).get("onlineEvent", {}).get("url", "")

    ticket_classes = server_data.get("event_listing_response", {}).get("tickets", {}).get("ticketClasses", [])
    if ticket_classes:
        first = ticket_classes[0]
        total_cost = first.get("totalCost", {})
        ticket_info = {
            "name": first.get("name", "General Admission"),
            "price": float(total_cost.get("majorValue", "0.0")),
            "currency": total_cost.get("currency", "USD"),
            "remaining": first.get("quantityRemaining", -1)
        }
        price_text = f"{ticket_info['price']} {ticket_info['currency']}"
    else:
        ticket_info = {
            "name": "General Admission",
            "price": 0.0,
            "currency": "USD",
            "remaining": -1
        }
        price_text = "Free"

    # ✅ Safe category handling
    format_name = safe_get_name(event.get("format"))
    category_name = safe_get_name(event.get("category"))
    subcategory_name = safe_get_name(event.get("subcategory"))

    categories = list(filter(None, [format_name, category_name, subcategory_name]))

    start_utc = event.get("start", {}).get("utc")
    end_utc = event.get("end", {}).get("utc")
    if not start_utc:
        return None  # Skip events without a start date
    if start_utc and end_utc:
        try:
            start_dt = datetime.fromisoformat(start_utc)
            end_dt = datetime.fromisoformat(end_utc)
            duration = int((end_dt - start_dt).total_seconds() // 60)
        except Exception:
            duration = 120
    else:
        duration = 120
    if duration <= 0 or duration > 20160:
        return None  # Skip events with abnormal duration

    return {
        "eventId": event.get("id") or str(uuid4()),
        "eventName": event.get("name", "Untitled Event").strip(),
        "location": location,
        "startTime": start_utc,
        "duration": duration,
        "categories": categories,
        "isOnline": event.get("isOnlineEvent", False),
        "joinLink": join_link,
        "imageUrl": image_url,
        "createdBy": organizer_name,
        "createdByEmail": "scraper@eventbrite.com",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "description": description or "No description available",
        "rsvpList": [],
        "origin": "external",
        "source": "eventbrite",
        "originalId": event.get("id"),
        "price": price_text,
        "ticket": ticket_info,
        "format": format_name or "Event",
        "category": category_name or "General",
        "subCategory": subcategory_name or "",
        "tags": tags,
        # Archive/status fields
        "isArchived": False,
        "archivedAt": None,
        "archivedBy": None,
        "archiveReason": None,
    }