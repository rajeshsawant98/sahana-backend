from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.models.pagination import CursorInfo, CursorPaginationParams
from app.repositories.events.event_mapper import parse_datetime, row_to_event_dict
from app.utils.logger import get_repository_logger


class EventRsvpRepository:
    """Repository for RSVP-related operations."""

    def __init__(self):
        self.logger = get_repository_logger(__name__)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _rsvp_row_to_dict(self, row) -> Dict[str, Any]:
        d = {"email": row.user_email, "status": row.status}
        if row.rating is not None:
            d["rating"] = row.rating
        if row.review is not None:
            d["review"] = row.review
        return d

    # ─── Status setters ───────────────────────────────────────────────────────

    async def join_rsvp(self, event_id: str, user_email: str) -> bool:
        return await self._set_rsvp_status(event_id, user_email, "joined")

    async def interested_rsvp(self, event_id: str, user_email: str) -> bool:
        return await self._set_rsvp_status(event_id, user_email, "interested")

    async def rsvp_to_event(self, event_id: str, user_email: str) -> bool:
        """Legacy join method kept for backward compatibility."""
        return await self.join_rsvp(event_id, user_email)

    async def _set_rsvp_status(self, event_id: str, user_email: str, status: str) -> bool:
        """
        Upsert RSVP row — replaces the Firestore read-modify-write of the entire
        rsvpList array. Clears rating/review when moving to non-attended status.
        """
        try:
            async with AsyncSessionLocal() as session:
                # Verify event exists
                exists = await session.scalar(
                    text("SELECT 1 FROM events WHERE event_id = :eid"),
                    {"eid": event_id}
                )
                if not exists:
                    self.logger.warning(f"Event {event_id} not found for RSVP")
                    return False

                await session.execute(text("""
                    INSERT INTO rsvps (event_id, user_email, status)
                    VALUES (:eid, :email, :status)
                    ON CONFLICT (event_id, user_email) DO UPDATE SET
                        status     = EXCLUDED.status,
                        rating     = CASE WHEN EXCLUDED.status = 'attended' THEN rsvps.rating  ELSE NULL END,
                        review     = CASE WHEN EXCLUDED.status = 'attended' THEN rsvps.review ELSE NULL END,
                        updated_at = NOW()
                """), {"eid": event_id, "email": user_email, "status": status})
                await session.commit()

            self.logger.info(f"User {user_email} RSVP'd to event {event_id} as {status}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting RSVP status for {user_email} → {event_id}: {e}", exc_info=True)
            return False

    # ─── Cancellers ───────────────────────────────────────────────────────────

    async def cancel_joined_rsvp(self, event_id: str, user_email: str) -> bool:
        return await self._cancel_rsvp_by_status(event_id, user_email, "joined")

    async def cancel_interested_rsvp(self, event_id: str, user_email: str) -> bool:
        return await self._cancel_rsvp_by_status(event_id, user_email, "interested")

    async def _cancel_rsvp_by_status(self, event_id: str, user_email: str, status: str) -> bool:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    DELETE FROM rsvps
                    WHERE event_id = :eid AND user_email = :email AND status = :status
                """), {"eid": event_id, "email": user_email, "status": status})
                await session.commit()
                removed = result.rowcount > 0
            if not removed:
                self.logger.warning(f"No '{status}' RSVP for {user_email} in event {event_id}")
            return removed
        except Exception as e:
            self.logger.error(f"Error cancelling '{status}' RSVP for {user_email}: {e}", exc_info=True)
            return False

    async def cancel_rsvp(self, event_id: str, user_email: str) -> bool:
        """Remove RSVP regardless of status."""
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("""
                    DELETE FROM rsvps WHERE event_id = :eid AND user_email = :email
                """), {"eid": event_id, "email": user_email})
                await session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling RSVP for {user_email}: {e}", exc_info=True)
            return False

    # ─── Update ───────────────────────────────────────────────────────────────

    async def update_rsvp_status(
        self, event_id: str, user_email: str, status: str,
        rating: Optional[int] = None, review: Optional[str] = None
    ) -> bool:
        try:
            # Resolve rating/review in Python to avoid SQL CASE type inference issues
            resolved_rating = int(rating) if status == "attended" and rating is not None else None
            resolved_review = review if status == "attended" else None

            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    UPDATE rsvps SET
                        status     = :status,
                        rating     = :rating,
                        review     = :review,
                        updated_at = NOW()
                    WHERE event_id = :eid AND user_email = :email
                """), {
                    "eid": event_id, "email": user_email,
                    "status": status, "rating": resolved_rating, "review": resolved_review,
                })
                await session.commit()
                updated = result.rowcount > 0
            self.logger.info(f"RSVP status updated: {user_email} → {event_id} = {status}")
            return updated
        except Exception as e:
            self.logger.error(f"Error updating RSVP status for {user_email}: {e}", exc_info=True)
            return False

    # ─── Getters ──────────────────────────────────────────────────────────────

    async def get_rsvp_count(self, event_id: str) -> int:
        try:
            async with AsyncSessionLocal() as session:
                count = await session.scalar(
                    text("SELECT COUNT(*) FROM rsvps WHERE event_id = :eid"),
                    {"eid": event_id}
                )
                return int(count or 0)
        except Exception as e:
            self.logger.error(f"Error getting RSVP count for event {event_id}: {e}", exc_info=True)
            return 0

    async def get_rsvp_list(self, event_id: str) -> List[Dict[str, Any]]:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT user_email, status, rating, review
                    FROM rsvps WHERE event_id = :eid
                """), {"eid": event_id})
                return [self._rsvp_row_to_dict(r) for r in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting RSVP list for event {event_id}: {e}", exc_info=True)
            return []

    async def get_rsvp_statistics(self, event_id: str) -> Dict[str, Any]:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT user_email, status, rating, review
                    FROM rsvps WHERE event_id = :eid
                """), {"eid": event_id})
                rsvp_list = [self._rsvp_row_to_dict(r) for r in result.fetchall()]
            return {"total_rsvps": len(rsvp_list), "rsvp_list": rsvp_list}
        except Exception as e:
            self.logger.error(f"Error getting RSVP statistics for event {event_id}: {e}", exc_info=True)
            return {"total_rsvps": 0, "rsvp_list": []}

    async def get_user_rsvps(self, user_email: str) -> List[Dict[str, Any]]:
        """
        Get all non-archived events a user has RSVP'd to.
        Replaces a full 53K-event collection scan with a single indexed JOIN.
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT e.*
                    FROM events e
                    JOIN rsvps r ON r.event_id = e.event_id
                    WHERE r.user_email = :email
                      AND e.is_archived = FALSE
                    ORDER BY e.start_time ASC
                """), {"email": user_email})
                return [row_to_event_dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting user RSVPs for {user_email}: {e}", exc_info=True)
            return []

    async def get_user_rsvps_paginated(
        self, user_email: str, cursor_params: Optional[CursorPaginationParams] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Cursor-paginated RSVPs for a user, optionally filtered by status."""
        try:
            page_size = cursor_params.page_size if cursor_params else 20
            params: Dict[str, Any] = {"email": user_email, "limit": page_size + 1}
            cursor_clause = ""
            status_clause = ""

            if status:
                status_clause = "AND r.status = :status"
                params["status"] = status

            if cursor_params and cursor_params.cursor:
                cursor_info = CursorInfo.decode(cursor_params.cursor)
                if cursor_info and cursor_info.start_time:
                    cursor_clause = """
                        AND (e.start_time > :cursor_time
                             OR (e.start_time = :cursor_time AND e.event_id > :cursor_id))
                    """
                    params["cursor_time"] = parse_datetime(cursor_info.start_time)
                    params["cursor_id"] = cursor_info.event_id

            async with AsyncSessionLocal() as session:
                result = await session.execute(text(f"""
                    SELECT e.*
                    FROM events e
                    JOIN rsvps r ON r.event_id = e.event_id
                    WHERE r.user_email = :email
                      AND e.is_archived = FALSE
                      {status_clause}
                      {cursor_clause}
                    ORDER BY e.start_time ASC, e.event_id ASC
                    LIMIT :limit
                """), params)
                rows = result.fetchall()

            events = [row_to_event_dict(row) for row in rows]
            has_next = len(events) > page_size
            if has_next:
                events = events[:page_size]

            next_cursor = None
            if has_next and events:
                last = events[-1]
                next_cursor = CursorInfo(
                    start_time=last.get("startTime"),
                    event_id=last.get("eventId")
                ).encode()

            return events, next_cursor
        except Exception as e:
            self.logger.error(f"Error getting paginated RSVPs for {user_email}: {e}")
            raise
