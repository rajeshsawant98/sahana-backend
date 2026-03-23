from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.models.pagination import CursorInfo, CursorPaginationParams, EventFilters
from app.repositories.events.event_mapper import parse_datetime, row_to_event_dict
from app.utils.logger import get_repository_logger


_STATE_FULL_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}


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
            conditions.append(
                "(LOWER(e.city) = LOWER(:city)"
                " OR LOWER(COALESCE(e.formatted_address, '')) LIKE '%' || LOWER(:city) || '%')"
            )
            params["city"] = filters.city
        if filters.state:
            state_full = _STATE_FULL_NAMES.get(filters.state.upper(), filters.state)
            conditions.append(
                "(LOWER(e.state) = LOWER(:state)"
                " OR LOWER(e.state) = LOWER(:state_full)"
                " OR LOWER(COALESCE(e.formatted_address, '')) LIKE '%' || LOWER(:state_full) || '%')"
            )
            params["state"] = filters.state
            params["state_full"] = state_full
        if filters.category:
            # Use array overlap operator so PostgreSQL can use the GIN index on categories.
            # Normalise to lowercase on both sides since categories are mixed-case in DB.
            conditions.append(
                "array(SELECT LOWER(x) FROM unnest(e.categories) x) @> ARRAY[LOWER(:category)]"
            )
            params["category"] = filters.category
        if filters.is_online is not None:
            conditions.append("e.is_online = :is_online")
            params["is_online"] = filters.is_online
        if filters.creator_email:
            conditions.append("LOWER(e.created_by_email) = LOWER(:creator_email)")
            params["creator_email"] = filters.creator_email
        if filters.keywords:
            # Use OR between terms so any matching word is sufficient.
            # "baseball games Sports" → "baseball OR games OR Sports"
            # → websearch_to_tsquery produces 'baseball' | 'game' | 'sport'
            kw_or = " OR ".join(filters.keywords.split())
            conditions.append("e.search_vector @@ websearch_to_tsquery('english', :keywords)")
            params["keywords"] = kw_or
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
                    ORDER BY start_time ASC NULLS LAST, event_id ASC
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
                    ORDER BY start_time ASC NULLS LAST, event_id ASC
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
                    WHERE event_id IN (
                        SELECT event_id FROM events
                        WHERE is_archived = TRUE AND start_time < :today
                        LIMIT 5000
                    )
                """), {"today": today})
                await session.commit()
                count = result.rowcount
            self.logger.info(f"Deleted {count} old events")
            return count
        except Exception as e:
            self.logger.error(f"Error deleting old events: {e}", exc_info=True)
            return 0

    async def search_events_by_embedding(
        self,
        query_embedding: list,
        parsed,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Semantic event search using pgvector cosine similarity.
        Hard filters (city, state, date, is_online) from ParsedSearchQuery are applied as WHERE clauses.
        Results are ordered by vector distance (most similar first).
        """
        try:
            params: Dict[str, Any] = {
                "query_vec": str(query_embedding),
                "limit": limit,
                "city": parsed.city,
                "state": parsed.state,
                "start_date": parsed.start_date,
                "end_date": parsed.end_date,
                "is_online": parsed.is_online,
            }
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT e.*,
                           1 - (e.embedding <=> CAST(:query_vec AS vector)) AS similarity_score
                    FROM events e
                    WHERE e.is_archived = FALSE
                      AND e.embedding IS NOT NULL
                      AND (:city IS NULL OR LOWER(e.city) = LOWER(:city))
                      AND (:state IS NULL OR LOWER(e.state) = LOWER(:state))
                      AND (:start_date IS NULL OR e.start_time >= CAST(:start_date AS timestamptz))
                      AND (:end_date IS NULL OR e.start_time <= CAST(:end_date AS timestamptz))
                      AND (:is_online IS NULL OR e.is_online = :is_online)
                    ORDER BY e.embedding <=> CAST(:query_vec AS vector) ASC
                    LIMIT :limit
                """), params)
                rows = result.mappings().fetchall()
                events = []
                for row in rows:
                    event = row_to_event_dict(row)
                    event["similarity_score"] = row.get("similarity_score")
                    events.append(event)
                return events
        except Exception as e:
            self.logger.error(f"Error in semantic event search: {e}", exc_info=True)
            return []
