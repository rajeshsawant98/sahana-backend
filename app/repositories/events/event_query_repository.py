from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.models.pagination import CursorInfo, CursorPaginationParams, EventFilters
from app.repositories.events.event_mapper import parse_datetime, row_to_event_dict
from app.utils.logger import get_repository_logger


class EventQueryRepository:
    """Repository for complex event queries and filtering operations."""

    def __init__(self):
        self.logger = get_repository_logger(__name__)

    # ─── Shared cursor pagination helper ──────────────────────────────────────

    async def _paginate_events(
        self,
        cursor_params: CursorPaginationParams,
        extra_where: str = "",
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """
        Generic keyset cursor pagination over events.

        extra_where: additional AND conditions (not including is_archived)
        extra_params: bind params for extra_where
        """
        cursor_info = None
        if cursor_params.cursor:
            cursor_info = CursorInfo.decode(cursor_params.cursor)
            if not cursor_info:
                raise ValueError("Invalid cursor format")

        params: Dict[str, Any] = {"limit": cursor_params.page_size + 1}
        if extra_params:
            params.update(extra_params)

        cursor_clause = ""
        if cursor_info and cursor_info.start_time:
            cursor_dt = parse_datetime(cursor_info.start_time)
            if cursor_params.direction == "next":
                cursor_clause = """
                    AND (e.start_time > :cursor_time
                         OR (e.start_time = :cursor_time AND e.event_id > :cursor_id))
                """
            else:
                cursor_clause = """
                    AND (e.start_time < :cursor_time
                         OR (e.start_time = :cursor_time AND e.event_id < :cursor_id))
                """
            params["cursor_time"] = cursor_dt
            params["cursor_id"] = cursor_info.event_id

        order = "ASC" if cursor_params.direction == "next" else "DESC"

        sql = f"""
            SELECT e.*
            FROM events e
            WHERE e.is_archived = FALSE
              {extra_where}
              {cursor_clause}
            ORDER BY e.start_time {order} NULLS LAST, e.event_id {order}
            LIMIT :limit
        """

        async with AsyncSessionLocal() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()

        events = [row_to_event_dict(row) for row in rows]

        if cursor_params.direction == "prev":
            events.reverse()

        has_more = len(events) > cursor_params.page_size
        if has_more:
            if cursor_params.direction == "next":
                events = events[:cursor_params.page_size]
            else:
                events = events[-cursor_params.page_size:]

        has_next = has_more if cursor_params.direction == "next" else cursor_params.cursor is not None
        has_prev = cursor_params.cursor is not None if cursor_params.direction == "next" else has_more

        next_cursor = prev_cursor = None
        if events:
            if has_next:
                next_cursor = CursorInfo(
                    start_time=events[-1].get("startTime"),
                    event_id=events[-1].get("eventId")
                ).encode()
            if has_prev:
                prev_cursor = CursorInfo(
                    start_time=events[0].get("startTime"),
                    event_id=events[0].get("eventId")
                ).encode()

        return events, next_cursor, prev_cursor, has_next, has_prev

    # ─── Filter builder ───────────────────────────────────────────────────────

    def _build_filter_clause(
        self, filters: Optional[EventFilters]
    ) -> Tuple[str, Dict[str, Any]]:
        """Convert EventFilters → (WHERE clause fragment, params dict)."""
        conditions, params = [], {}
        if not filters:
            return "", {}

        if filters.city:
            conditions.append("LOWER(e.city) = LOWER(:city)")
            params["city"] = filters.city
        if filters.state:
            conditions.append("LOWER(e.state) = LOWER(:state)")
            params["state"] = filters.state
        if filters.category:
            conditions.append("EXISTS (SELECT 1 FROM unnest(e.categories) c WHERE LOWER(c) = LOWER(:category))")
            params["category"] = filters.category
        if filters.is_online is not None:
            conditions.append("e.is_online = :is_online")
            params["is_online"] = filters.is_online
        if filters.creator_email:
            conditions.append("LOWER(e.created_by_email) = LOWER(:creator_email)")
            params["creator_email"] = filters.creator_email
        if filters.start_date:
            conditions.append("e.start_time >= :start_date")
            params["start_date"] = parse_datetime(filters.start_date)
        if filters.end_date:
            conditions.append("e.start_time <= :end_date")
            params["end_date"] = parse_datetime(filters.end_date)

        clause = (" AND " + " AND ".join(conditions)) if conditions else ""
        return clause, params

    # ─── Public methods ───────────────────────────────────────────────────────

    async def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all non-archived events (hard-capped at 5000 for admin use)."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT * FROM events
                    WHERE is_archived = FALSE
                    ORDER BY start_time ASC NULLS LAST
                    LIMIT 5000
                """))
                return [row_to_event_dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting all events: {e}", exc_info=True)
            return []

    async def get_all_events_paginated(
        self,
        cursor_params: CursorPaginationParams,
        filters: Optional[EventFilters] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        try:
            extra_where, params = self._build_filter_clause(filters)
            return await self._paginate_events(cursor_params, extra_where, params)
        except Exception as e:
            self.logger.error(f"Error in cursor pagination: {e}", exc_info=True)
            return [], None, None, False, False

    async def get_nearby_events_paginated(
        self, city: str, state: str, cursor_params: CursorPaginationParams
    ) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Non-archived community + external events in a city/state."""
        try:
            extra_where = "AND LOWER(e.city) = LOWER(:city) AND LOWER(e.state) = LOWER(:state) AND e.origin IN ('manual', 'external', 'community')"
            params = {"city": city, "state": state}
            return await self._paginate_events(cursor_params, extra_where, params)
        except Exception as e:
            self.logger.error(f"Error in nearby events pagination: {e}", exc_info=True)
            return [], None, None, False, False

    async def get_external_events(self, city: str, state: str) -> List[Dict[str, Any]]:
        """Non-paginated external events for a city/state (capped at 200)."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT * FROM events
                    WHERE is_archived = FALSE
                      AND LOWER(city) = LOWER(:city) AND LOWER(state) = LOWER(:state)
                      AND origin = 'external'
                    ORDER BY start_time ASC NULLS LAST
                    LIMIT 200
                """), {"city": city, "state": state})
                return [row_to_event_dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting external events: {e}", exc_info=True)
            return []

    async def get_external_events_paginated(
        self, city: str, state: str, cursor_params: CursorPaginationParams
    ) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        try:
            extra_where = "AND LOWER(e.city) = LOWER(:city) AND LOWER(e.state) = LOWER(:state) AND e.origin = 'external'"
            params = {"city": city, "state": state}
            return await self._paginate_events(cursor_params, extra_where, params)
        except Exception as e:
            self.logger.error(f"Error in external events pagination: {e}", exc_info=True)
            return [], None, None, False, False

    async def get_events_for_archiving(self) -> List[Dict[str, Any]]:
        """Events whose end time has passed and are not yet archived."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT * FROM events
                    WHERE is_archived = FALSE
                      AND start_time + (duration * interval '1 second') < NOW()
                    LIMIT 1000
                """))
                return [row_to_event_dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting events for archiving: {e}", exc_info=True)
            return []

    async def delete_events_before_today(self) -> int:
        """Delete archived events whose start_time is before today."""
        try:
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    DELETE FROM events
                    WHERE is_archived = TRUE AND start_time < :today
                """), {"today": today})
                await session.commit()
                count = result.rowcount
            self.logger.info(f"Deleted {count} old events")
            return count
        except Exception as e:
            self.logger.error(f"Error deleting old events: {e}", exc_info=True)
            return 0
