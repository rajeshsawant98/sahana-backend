from datetime import datetime, timezone
from typing import Dict, Optional
from urllib.parse import urlparse
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

def _safe_name(value) -> str:
    return value.get("name", "") if isinstance(value, dict) else str(value or "")


def parse_eventbrite_server_data(data: dict, url: str) -> Optional[dict]:
    """
    Parses Eventbrite `window.__SERVER_DATA__` (or similar SSR blobs) into Sahana format.
    Handles both the legacy structure and common Next.js pageProps variants.
    Returns None if the event is missing a start date or has an abnormal duration (> 20160 min).
    """
    # Support both top-level "event" key and unwrapped dicts
    event = data.get("event") if "event" in data else data
    components = data.get("components", {})

    if not isinstance(event, dict):
        return None

    start_utc = event.get("start", {}).get("utc") or event.get("startDate") or event.get("start_date")
    end_utc = event.get("end", {}).get("utc") or event.get("endDate") or event.get("end_date")

    if not start_utc:
        return None

    try:
        start_dt = datetime.fromisoformat(start_utc.replace("Z", "+00:00"))
    except Exception:
        return None

    duration = 120
    if end_utc:
        try:
            end_dt = datetime.fromisoformat(end_utc.replace("Z", "+00:00"))
            duration = int((end_dt - start_dt).total_seconds() // 60)
            if duration <= 0 or duration > 20160:
                return None
        except Exception:
            pass

    # Location — try components.eventMap first, then event.venue
    event_map = components.get("eventMap", {})
    venue = event.get("venue", {}) if isinstance(event.get("venue"), dict) else {}

    venue_name = (
        event_map.get("venueName")
        or venue.get("name")
        or "Unknown Venue"
    )
    city = (
        (venue.get("address", {}).get("city") if isinstance(venue.get("address"), dict) else None)
        or venue.get("city")
        or ""
    )
    state = venue.get("region") or venue.get("address", {}).get("region", "") if isinstance(venue.get("address"), dict) else venue.get("region", "")
    formatted = (
        (venue.get("address", {}).get("localized_address_display") if isinstance(venue.get("address"), dict) else None)
        or event_map.get("venueAddress")
        or "N/A"
    )
    geo = event_map.get("location", {})
    try:
        lat = float(geo.get("latitude", 0.0))
        lng = float(geo.get("longitude", 0.0))
    except (TypeError, ValueError):
        lat, lng = 0.0, 0.0

    location = {
        "name": venue_name,
        "city": city,
        "state": state,
        "country": "United States",
        "latitude": lat,
        "longitude": lng,
        "formattedAddress": formatted,
    }

    # Categories — format / category / subcategory
    format_name = _safe_name(event.get("format"))
    category_name = _safe_name(event.get("category"))
    subcategory_name = _safe_name(event.get("subcategory"))
    categories = [n for n in [format_name, category_name, subcategory_name] if n] or ["General"]

    # Tags
    tags = [
        t.get("text") for t in components.get("tags", [])
        if isinstance(t, dict) and t.get("text")
    ]

    # Organizer
    organizer_name = (
        components.get("organizer", {}).get("name")
        or event.get("organizer", {}).get("name")
        or "Eventbrite Organizer"
    ) if isinstance(event.get("organizer"), dict) else "Eventbrite Organizer"

    # Image
    image_url = (
        data.get("event_listing_response", {}).get("schemaInfo", {}).get("schemaImageUrl")
        or (event.get("logo", {}).get("url") if isinstance(event.get("logo"), dict) else None)
        or ""
    )

    # Description
    description = (
        components.get("eventDescription", {}).get("summary")
        or event.get("description", {}).get("text") if isinstance(event.get("description"), dict) else None
        or event.get("summary")
        or "No description available"
    )

    is_online = bool(event.get("isOnlineEvent") or event.get("online_event"))

    event_id = event.get("id") or url.rstrip("/").split("?")[0].rstrip("/").split("-")[-1] or str(uuid4())

    return {
        "eventId": str(event_id),
        "eventName": (event.get("name", {}).get("text") if isinstance(event.get("name"), dict) else event.get("name") or "Untitled Event").strip(),
        "location": location,
        "startTime": start_utc,
        "duration": duration,
        "categories": categories,
        "isOnline": is_online,
        "joinLink": event.get("url") or url,
        "imageUrl": image_url,
        "createdBy": organizer_name,
        "createdByEmail": "scraper@eventbrite.com",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "description": description,
        "rsvpList": [],
        "origin": "external",
        "source": "eventbrite",
        "originalId": str(event_id),
        "tags": tags,
        "format": format_name or "Event",
        "category": category_name or "General",
        "subCategory": subcategory_name or "",
        "isArchived": False,
        "archivedAt": None,
        "archivedBy": None,
        "archiveReason": None,
    }


# All Schema.org subtypes of Event that Eventbrite uses
_SCHEMA_EVENT_TYPES = {
    "Event", "Festival", "SocialEvent", "BusinessEvent", "ChildrensEvent",
    "ComedyEvent", "DanceEvent", "EducationEvent", "ExhibitionEvent",
    "FoodEvent", "Hackathon", "LiteraryEvent", "MusicEvent", "SaleEvent",
    "ScreeningEvent", "SportsEvent", "TheaterEvent", "VisualArtsEvent",
}


def is_schema_event(jsonld: dict) -> bool:
    return jsonld.get("@type") in _SCHEMA_EVENT_TYPES


def parse_eventbrite_jsonld(jsonld: dict, url: str, extra_categories: list[str] | None = None) -> Optional[dict]:
    """
    Parses an Eventbrite JSON-LD Event (or any Schema.org Event subtype) into Sahana format.
    Returns None if the event is missing a start date or has an abnormal duration (> 20160 min).

    extra_categories: categories extracted from the listing page DOM (data-event-category attr).
    """
    start_str = jsonld.get("startDate", "")
    end_str = jsonld.get("endDate", "")

    if not start_str:
        return None

    try:
        start_dt = datetime.fromisoformat(start_str)
        start_utc = start_dt.isoformat()
    except Exception:
        return None

    duration = 120
    if end_str:
        try:
            end_dt = datetime.fromisoformat(end_str)
            duration = int((end_dt - start_dt).total_seconds() // 60)
            if duration <= 0 or duration > 20160:
                return None
        except Exception:
            pass

    # Location
    loc = jsonld.get("location", {})
    if isinstance(loc, dict):
        addr = loc.get("address", {})
        venue_name = loc.get("name", "Unknown Venue")
        if isinstance(addr, dict):
            city = addr.get("addressLocality", "")
            state = addr.get("addressRegion", "")
            formatted = addr.get("streetAddress", "N/A")
        else:
            city = ""
            state = ""
            formatted = str(addr) if addr else "N/A"
        geo = loc.get("geo", {})
        lat = float(geo.get("latitude", 0.0)) if isinstance(geo, dict) else 0.0
        lng = float(geo.get("longitude", 0.0)) if isinstance(geo, dict) else 0.0
    else:
        venue_name, city, state, formatted, lat, lng = "Unknown Venue", "", "", "N/A", 0.0, 0.0

    location = {
        "name": venue_name,
        "city": city,
        "state": state,
        "country": "United States",
        "latitude": lat,
        "longitude": lng,
        "formattedAddress": formatted,
    }

    # Organizer
    organizer = jsonld.get("organizer", {})
    if isinstance(organizer, list):
        organizer = organizer[0] if organizer else {}
    organizer_name = organizer.get("name", "Eventbrite Organizer") if isinstance(organizer, dict) else "Eventbrite Organizer"

    # Categories: prefer listing-page data-event-category, fall back to @type, then keywords
    if extra_categories:
        categories = [c.title() for c in extra_categories if c]
    else:
        schema_type = jsonld.get("@type", "")
        keywords = jsonld.get("keywords", "")
        from_keywords = [k.strip() for k in keywords.split(",") if k.strip()]
        # Use schema @type only when it's a specific subtype (not generic "Event")
        type_cat = [schema_type] if schema_type and schema_type != "Event" else []
        categories = from_keywords or type_cat or ["General"]

    # Image
    image = jsonld.get("image", "")
    if isinstance(image, list):
        image = image[0] if image else ""
    if isinstance(image, dict):
        image = image.get("url", "")

    # Price from offers
    price_text = "Free"
    offers = jsonld.get("offers")
    if isinstance(offers, list) and offers:
        offers = offers[0]
    if isinstance(offers, dict):
        low = offers.get("lowPrice", "0")
        currency = offers.get("priceCurrency", "USD")
        try:
            price_text = "Free" if float(low) == 0 else f"{float(low):.2f} {currency}"
        except (ValueError, TypeError):
            pass

    is_online = "OnlineEventAttendanceMode" in jsonld.get("eventAttendanceMode", "")

    canonical_url = jsonld.get("url") or url.rstrip("/").split("?")[0]
    # Extract numeric ticket ID from the URL path slug (e.g. "event-name-tickets-1234" → "1234")
    path_segment = urlparse(canonical_url).path.rstrip("/").split("/")[-1]
    event_id = path_segment.split("-")[-1] if path_segment else str(uuid4())

    return {
        "eventId": event_id,
        "eventName": jsonld.get("name", "Untitled Event").strip(),
        "location": location,
        "startTime": start_utc,
        "duration": duration,
        "categories": categories,
        "isOnline": is_online,
        "joinLink": canonical_url,
        "imageUrl": image,
        "createdBy": organizer_name,
        "createdByEmail": "scraper@eventbrite.com",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "description": jsonld.get("description", "No description available"),
        "price": price_text,
        "rsvpList": [],
        "origin": "external",
        "source": "eventbrite",
        "originalId": event_id,
        "isArchived": False,
        "archivedAt": None,
        "archivedBy": None,
        "archiveReason": None,
    }