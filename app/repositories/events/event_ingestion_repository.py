from typing import Any, Dict, Optional

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.repositories.events.event_mapper import parse_datetime
from app.utils.logger import get_repository_logger


class EventIngestionRepository:
    """Repository for external event ingestion (Ticketmaster, Eventbrite)."""

    def __init__(self):
        self.logger = get_repository_logger(__name__)

    async def save_event(self, event: dict) -> bool:
        """
        Upsert a single scraped event.
        Uses ON CONFLICT (event_id) DO NOTHING — idempotent, replaces Firestore .set(merge=True).
        original_id UNIQUE constraint provides a second dedup guard for the ingestion service.
        """
        loc = event.get("location") or {}
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("""
                    INSERT INTO events (
                        event_id, event_name, description,
                        latitude, longitude, city, state, country,
                        formatted_address, location_name,
                        start_time, duration, categories,
                        is_online, join_link, image_url,
                        created_by, created_by_email,
                        origin, source, original_id,
                        tags, price, format, sub_category,
                        is_archived
                    ) VALUES (
                        :event_id, :event_name, :description,
                        :latitude, :longitude, :city, :state, :country,
                        :formatted_address, :location_name,
                        :start_time, :duration, :categories,
                        :is_online, :join_link, :image_url,
                        :created_by, :created_by_email,
                        :origin, :source, :original_id,
                        :tags, :price, :format, :sub_category,
                        FALSE
                    )
                    ON CONFLICT (event_id) DO NOTHING
                """), {
                    "event_id":         event.get("eventId"),
                    "event_name":       event.get("eventName", "Untitled Event"),
                    "description":      event.get("description", "No description available"),
                    "latitude":         loc.get("latitude"),
                    "longitude":        loc.get("longitude"),
                    "city":             loc.get("city"),
                    "state":            loc.get("state"),
                    "country":          loc.get("country"),
                    "formatted_address": loc.get("formattedAddress"),
                    "location_name":    loc.get("name"),
                    "start_time":       parse_datetime(event.get("startTime")),
                    "duration":         event.get("duration"),
                    "categories":       event.get("categories") or [],
                    "is_online":        event.get("isOnline", False),
                    "join_link":        event.get("joinLink") or None,
                    "image_url":        event.get("imageUrl") or None,
                    "created_by":       event.get("createdBy"),
                    "created_by_email": event.get("createdByEmail"),
                    "origin":           event.get("origin", "external"),
                    "source":           event.get("source"),
                    "original_id":      event.get("originalId") or None,
                    "tags":             event.get("tags") or [],
                    "price":            event.get("price") or None,
                    "format":           event.get("format") or None,
                    "sub_category":     event.get("subCategory") or None,
                })
                await session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to save event {event.get('eventName', '?')}: {e}")
            return False

    async def save_bulk_events(self, events: list[dict]) -> int:
        """Batch INSERT all events in a single query. Returns count of newly inserted rows."""
        if not events:
            return 0

        rows = []
        for event in events:
            loc = event.get("location") or {}
            rows.append({
                "event_id":         event.get("eventId"),
                "event_name":       event.get("eventName", "Untitled Event"),
                "description":      event.get("description", "No description available"),
                "latitude":         loc.get("latitude"),
                "longitude":        loc.get("longitude"),
                "city":             loc.get("city"),
                "state":            loc.get("state"),
                "country":          loc.get("country"),
                "formatted_address": loc.get("formattedAddress"),
                "location_name":    loc.get("name"),
                "start_time":       parse_datetime(event.get("startTime")),
                "duration":         event.get("duration"),
                "categories":       event.get("categories") or [],
                "is_online":        event.get("isOnline", False),
                "join_link":        event.get("joinLink") or None,
                "image_url":        event.get("imageUrl") or None,
                "created_by":       event.get("createdBy"),
                "created_by_email": event.get("createdByEmail"),
                "origin":           event.get("origin", "external"),
                "source":           event.get("source"),
                "original_id":      event.get("originalId") or None,
                "tags":             event.get("tags") or [],
                "price":            event.get("price") or None,
                "format":           event.get("format") or None,
                "sub_category":     event.get("subCategory") or None,
            })

        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    INSERT INTO events (
                        event_id, event_name, description,
                        latitude, longitude, city, state, country,
                        formatted_address, location_name,
                        start_time, duration, categories,
                        is_online, join_link, image_url,
                        created_by, created_by_email,
                        origin, source, original_id,
                        tags, price, format, sub_category,
                        is_archived
                    ) VALUES (
                        :event_id, :event_name, :description,
                        :latitude, :longitude, :city, :state, :country,
                        :formatted_address, :location_name,
                        :start_time, :duration, :categories,
                        :is_online, :join_link, :image_url,
                        :created_by, :created_by_email,
                        :origin, :source, :original_id,
                        :tags, :price, :format, :sub_category,
                        FALSE
                    )
                    ON CONFLICT (event_id) DO NOTHING
                """), rows)
                await session.commit()
                return result.rowcount
        except Exception as e:
            self.logger.error(f"Bulk insert failed ({len(events)} events): {e}")
            # Fall back to row-by-row so a single bad event doesn't drop the whole batch
            saved = 0
            for event in events:
                if await self.save_event(event):
                    saved += 1
            return saved

    async def get_by_original_id(self, original_id: str) -> Optional[Dict[str, Any]]:
        """
        Dedup check before insert.
        Replaces Firestore collection scan (where originalId == x) with a direct index lookup.
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text("SELECT event_id FROM events WHERE original_id = :oid LIMIT 1"),
                    {"oid": original_id}
                )
                row = result.fetchone()
                return {"event_id": row.event_id} if row else None
        except Exception as e:
            self.logger.error(f"Lookup by original_id failed: {e}")
            return None
