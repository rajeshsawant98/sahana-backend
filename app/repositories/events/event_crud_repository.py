import asyncio
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.repositories.events.event_mapper import build_update_params, parse_datetime, row_to_event_dict
from app.utils.logger import get_repository_logger


async def _embed_event(event_dict: Dict[str, Any]) -> None:
    """Background task: generate and store embedding for an event."""
    try:
        from app.services.embedding_service import generate_and_store_event_embedding
        await generate_and_store_event_embedding(event_dict)
    except Exception:
        pass  # non-critical — search falls back to SQL filters


class EventCrudRepository:
    """Repository for basic CRUD operations on events."""

    def __init__(self):
        self.logger = get_repository_logger(__name__)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    async def _fetch_organizers(self, session, event_id: str) -> List[str]:
        result = await session.execute(
            text("SELECT user_email FROM event_organizers WHERE event_id = :eid"),
            {"eid": event_id}
        )
        return [row.user_email for row in result.fetchall()]

    async def _fetch_moderators(self, session, event_id: str) -> List[str]:
        result = await session.execute(
            text("SELECT user_email FROM event_moderators WHERE event_id = :eid"),
            {"eid": event_id}
        )
        return [row.user_email for row in result.fetchall()]

    async def _fetch_rsvp_list(self, session, event_id: str) -> List[Dict[str, Any]]:
        result = await session.execute(
            text("SELECT user_email, status, rating, review FROM rsvps WHERE event_id = :eid"),
            {"eid": event_id}
        )
        rows = result.fetchall()
        rsvps = []
        for row in rows:
            r = {"email": row.user_email, "status": row.status}
            if row.rating is not None:
                r["rating"] = row.rating
            if row.review is not None:
                r["review"] = row.review
            rsvps.append(r)
        return rsvps

    # ─── CRUD ─────────────────────────────────────────────────────────────────

    async def create_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        event_id = str(uuid.uuid4())
        loc = data.get("location") or {}
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("""
                    INSERT INTO events (
                        event_id, event_name, description,
                        latitude, longitude, city, state, country, formatted_address, location_name,
                        start_time, duration, categories, is_online, join_link, image_url,
                        created_by, created_by_email,
                        origin, source,
                        is_archived
                    ) VALUES (
                        :event_id, :event_name, :description,
                        :latitude, :longitude, :city, :state, :country, :formatted_address, :location_name,
                        :start_time, :duration, :categories, :is_online, :join_link, :image_url,
                        :created_by, :created_by_email,
                        'community', 'user',
                        FALSE
                    )
                """), {
                    "event_id":         event_id,
                    "event_name":       data["eventName"],
                    "description":      data.get("description", "No description available"),
                    "latitude":         loc.get("latitude"),
                    "longitude":        loc.get("longitude"),
                    "city":             loc.get("city"),
                    "state":            loc.get("state"),
                    "country":          loc.get("country"),
                    "formatted_address": loc.get("formattedAddress"),
                    "location_name":    loc.get("name"),
                    "start_time":       parse_datetime(data.get("startTime")),
                    "duration":         data.get("duration"),
                    "categories":       data.get("categories", []),
                    "is_online":        data.get("isOnline", False),
                    "join_link":        data.get("joinLink") or None,
                    "image_url":        data.get("imageUrl") or None,
                    "created_by":       data.get("createdBy"),
                    "created_by_email": data.get("createdByEmail"),
                })

                # Organizers — batch insert
                organizers = data.get("organizers") or []
                if organizers:
                    await session.execute(text("""
                        INSERT INTO event_organizers (event_id, user_email)
                        VALUES (:eid, :email) ON CONFLICT DO NOTHING
                    """), [{"eid": event_id, "email": e} for e in organizers])

                # Moderators — batch insert
                moderators = data.get("moderators") or []
                if moderators:
                    await session.execute(text("""
                        INSERT INTO event_moderators (event_id, user_email)
                        VALUES (:eid, :email) ON CONFLICT DO NOTHING
                    """), [{"eid": event_id, "email": e} for e in moderators])

                await session.commit()

            # Fire-and-forget: generate embedding in background
            event_dict = {
                "event_id":   event_id,
                "event_name": data["eventName"],
                "description": data.get("description", ""),
                "categories": data.get("categories", []),
                "city":       loc.get("city"),
                "state":      loc.get("state"),
            }
            asyncio.create_task(_embed_event(event_dict))

            return {"eventId": event_id}
        except Exception as e:
            self.logger.error(f"Error creating event: {e}")
            raise

    async def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT
                        e.*,
                        COALESCE(
                            ARRAY_AGG(DISTINCT o.user_email) FILTER (WHERE o.user_email IS NOT NULL),
                            '{}'
                        ) AS organizers,
                        COALESCE(
                            ARRAY_AGG(DISTINCT m.user_email) FILTER (WHERE m.user_email IS NOT NULL),
                            '{}'
                        ) AS moderators,
                        COALESCE(
                            JSON_AGG(JSON_BUILD_OBJECT(
                                'email',  r.user_email,
                                'status', r.status,
                                'rating', r.rating,
                                'review', r.review
                            )) FILTER (WHERE r.user_email IS NOT NULL),
                            '[]'
                        ) AS rsvp_json
                    FROM events e
                    LEFT JOIN event_organizers o ON o.event_id = e.event_id
                    LEFT JOIN event_moderators m ON m.event_id = e.event_id
                    LEFT JOIN rsvps r ON r.event_id = e.event_id
                    WHERE e.event_id = :eid
                    GROUP BY e.event_id
                """), {"eid": event_id})
                row = result.fetchone()
                if not row:
                    return None
                d = row._mapping
                organizers = list(d.get("organizers") or [])
                moderators = list(d.get("moderators") or [])
                rsvp_list  = list(d.get("rsvp_json") or [])
                return row_to_event_dict(row, organizers, moderators, rsvp_list)
        except Exception as e:
            self.logger.error(f"Error getting event {event_id}: {e}")
            return None

    async def update_event(self, event_id: str, update_data: Dict[str, Any]) -> bool:
        params = build_update_params(update_data)
        if not params:
            return True

        set_clause = ", ".join(f"{col} = :{col}" for col in params)
        params["event_id"] = event_id
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text(f"UPDATE events SET {set_clause}, updated_at = NOW() WHERE event_id = :event_id"),
                    params
                )
                await session.commit()
                updated = result.rowcount > 0

            # Refresh embedding if any embedding-relevant field changed
            _EMBEDDING_FIELDS = {"event_name", "description", "categories", "city", "state"}
            if updated and _EMBEDDING_FIELDS.intersection(params):
                # Fetch the updated event to build embedding text
                event = await self.get_event_by_id(event_id)
                if event:
                    asyncio.create_task(_embed_event({
                        "event_id":    event_id,
                        "event_name":  event.get("eventName"),
                        "description": event.get("description"),
                        "categories":  event.get("categories", []),
                        "city":        event.get("location", {}).get("city"),
                        "state":       event.get("location", {}).get("state"),
                    }))

            return updated
        except Exception as e:
            self.logger.error(f"Error updating event {event_id}: {e}")
            return False

    async def delete_event(self, event_id: str) -> bool:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text("DELETE FROM events WHERE event_id = :eid"),
                    {"eid": event_id}
                )
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error deleting event {event_id}: {e}")
            return False

    async def update_event_roles(self, event_id: str, field: str, emails: List[str]) -> bool:
        """Replace organizers or moderators list for an event."""
        table = "event_organizers" if field == "organizers" else "event_moderators"
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    text(f"DELETE FROM {table} WHERE event_id = :eid"),
                    {"eid": event_id}
                )
                for email in emails:
                    await session.execute(text(f"""
                        INSERT INTO {table} (event_id, user_email)
                        VALUES (:eid, :email) ON CONFLICT DO NOTHING
                    """), {"eid": event_id, "email": email})
                await session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating {field} for event {event_id}: {e}")
            return False
