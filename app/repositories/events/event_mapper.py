"""
Shared helpers for converting Postgres rows ↔ the camelCase dict shape
that the service layer expects (matching the old Firestore format).
"""
import datetime
from typing import Any, Dict, List, Optional


def parse_datetime(value) -> datetime.datetime | None:
    """Parse an ISO datetime string or passthrough a datetime object."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value
    if isinstance(value, str):
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S.%f%z",
        ):
            try:
                dt = datetime.datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                return dt
            except ValueError:
                continue
    return None

# Flat snake_case column → camelCase key used by service layer
_COLUMN_TO_CAMEL = {
    "event_id":         "eventId",
    "event_name":       "eventName",
    "start_time":       "startTime",
    "is_online":        "isOnline",
    "join_link":        "joinLink",
    "image_url":        "imageUrl",
    "created_by":       "createdBy",
    "created_by_email": "createdByEmail",
    "is_archived":      "isArchived",
    "archived_at":      "archivedAt",
    "archived_by":      "archivedBy",
    "archive_reason":   "archiveReason",
    "unarchived_at":    "unarchivedAt",
    "created_at":       "createdAt",
    "updated_at":       "updatedAt",
    "sub_category":     "subCategory",
    "ticket_name":      "ticketName",
    "ticket_remaining": "ticketRemaining",
    "ticket_currency":  "ticketCurrency",
    "ticket_price":     "ticketPrice",
    "location_name":    "locationName",
    "formatted_address": "formattedAddress",
}

# camelCase key → flat snake_case column (for UPDATE)
_CAMEL_TO_COLUMN = {v: k for k, v in _COLUMN_TO_CAMEL.items()}
# Extra direct mappings from service layer update payloads
_CAMEL_TO_COLUMN.update({
    "eventName":    "event_name",
    "startTime":    "start_time",
    "isOnline":     "is_online",
    "joinLink":     "join_link",
    "imageUrl":     "image_url",
    "createdBy":    "created_by",
    "createdByEmail": "created_by_email",
    "isArchived":   "is_archived",
    "archivedAt":   "archived_at",
    "archivedBy":   "archived_by",
    "archiveReason": "archive_reason",
    "unarchivedAt": "unarchived_at",
    "subCategory":  "sub_category",
})

# Columns that live as flat fields in Postgres but are nested in location
_LOCATION_COLS = {"latitude", "longitude", "city", "state", "country",
                  "formatted_address", "location_name"}


def row_to_event_dict(
    row,
    organizers: Optional[List[str]] = None,
    moderators: Optional[List[str]] = None,
    rsvp_list: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Convert a DB row to the camelCase event dict the service layer expects."""
    d = dict(row._mapping)

    # Remove internal count column if present
    d.pop("_total", None)

    # Rebuild nested location object
    d["location"] = {
        "latitude":        d.pop("latitude", None),
        "longitude":       d.pop("longitude", None),
        "city":            d.pop("city", None),
        "state":           d.pop("state", None),
        "country":         d.pop("country", None),
        "formattedAddress": d.pop("formatted_address", None),
        "name":            d.pop("location_name", None),
    }

    # Rename snake_case → camelCase
    for col, camel in _COLUMN_TO_CAMEL.items():
        if col in d:
            d[camel] = d.pop(col)

    # Nest ticket fields (always pop, only create dict when at least one is set)
    ticket_name      = d.pop("ticketName", None)
    ticket_remaining = d.pop("ticketRemaining", None)
    ticket_currency  = d.pop("ticketCurrency", None)
    ticket_price_raw = d.pop("ticketPrice", None)
    ticket_price     = float(ticket_price_raw) if ticket_price_raw is not None else None
    if any(v is not None for v in (ticket_name, ticket_remaining, ticket_currency, ticket_price)):
        d["ticket"] = {
            "name":      ticket_name,
            "remaining": ticket_remaining,
            "currency":  ticket_currency,
            "price":     ticket_price,
        }

    # Convert datetime objects to ISO strings (match Firestore behaviour)
    for key in ("startTime", "archivedAt", "unarchivedAt", "createdAt", "updatedAt"):
        if d.get(key) is not None and hasattr(d[key], "isoformat"):
            d[key] = d[key].isoformat()

    # Inject related-table data
    d["organizers"] = organizers if organizers is not None else []
    d["moderators"] = moderators if moderators is not None else []
    d["rsvpList"]   = rsvp_list  if rsvp_list  is not None else []

    return d


def build_update_params(update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a camelCase update payload from the service layer into
    a dict of {sql_column: value} pairs suitable for a dynamic UPDATE.
    Handles nested location dict.
    """
    params: Dict[str, Any] = {}

    for key, value in update_data.items():
        if key == "location" and isinstance(value, dict):
            params["latitude"]          = value.get("latitude")
            params["longitude"]         = value.get("longitude")
            params["city"]              = value.get("city")
            params["state"]             = value.get("state")
            params["country"]           = value.get("country")
            params["formatted_address"] = value.get("formattedAddress")
            params["location_name"]     = value.get("name")
        elif key in _CAMEL_TO_COLUMN:
            col = _CAMEL_TO_COLUMN[key]
            # Parse datetime strings for TIMESTAMPTZ columns
            if col in ("start_time", "archived_at", "unarchived_at") and isinstance(value, str):
                value = parse_datetime(value)
            params[col] = value
        elif key in ("duration", "categories", "tags", "price",
                     "description", "origin", "source", "format"):
            params[key] = value
        # unknown keys are silently ignored

    return params
