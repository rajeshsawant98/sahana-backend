from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.models.pagination import CursorInfo, CursorPaginationParams
from app.repositories.events.event_mapper import parse_datetime, row_to_event_dict
from app.utils.logger import get_repository_logger


class EventUserRepository:
    """Repository for user-specific event queries."""

    def __init__(self):
        self.logger = get_repository_logger(__name__)

    # ─── Shared pagination helper ──────────────────────────────────────────────

    async def _paginate_user_events(
        self,
        sql_template: str,
        params: Dict[str, Any],
        cursor_params: Optional[CursorPaginationParams],
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Shared keyset cursor pagination for user-scoped event queries.

        sql_template must contain {cursor_clause} and {limit} placeholders
        and already include ORDER BY e.start_time ASC, e.event_id ASC.
        """
        page_size = cursor_params.page_size if cursor_params else 20
        params["limit"] = page_size + 1

        cursor_clause = ""
        if cursor_params and cursor_params.cursor:
            cursor_info = CursorInfo.decode(cursor_params.cursor)
            if cursor_info and cursor_info.start_time:
                cursor_clause = """
                    AND (e.start_time > :cursor_time
                         OR (e.start_time = :cursor_time AND e.event_id > :cursor_id))
                """
                params["cursor_time"] = parse_datetime(cursor_info.start_time)
                params["cursor_id"] = cursor_info.event_id

        sql = sql_template.format(cursor_clause=cursor_clause, limit=":limit")

        async with AsyncSessionLocal() as session:
            result = await session.execute(text(sql), params)
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
                event_id=last.get("eventId"),
            ).encode()

        return events, next_cursor

    # ─── Created by user ──────────────────────────────────────────────────────

    async def get_events_by_creator(self, email: str) -> List[Dict[str, Any]]:
        """Non-archived events created by email. Replaces Firestore where + Python filter."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT * FROM events
                    WHERE is_archived = FALSE AND created_by_email = :email
                    ORDER BY start_time ASC NULLS LAST, event_id ASC
                """), {"email": email})
                return [row_to_event_dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting events by creator {email}: {e}", exc_info=True)
            return []

    async def get_events_by_creator_paginated(
        self,
        email: str,
        cursor_params: Optional[CursorPaginationParams] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        try:
            sql = """
                SELECT e.* FROM events e
                WHERE e.is_archived = FALSE
                  AND e.created_by_email = :email
                  {cursor_clause}
                ORDER BY e.start_time ASC NULLS LAST, e.event_id ASC
                LIMIT {limit}
            """
            events, next_cursor = await self._paginate_user_events(
                sql, {"email": email}, cursor_params
            )
            self.logger.info(f"Retrieved {len(events)} events by creator {email}")
            return events, next_cursor
        except Exception as e:
            self.logger.error(f"Error getting paginated events by creator {email}: {e}")
            raise

    # ─── Organized by user ────────────────────────────────────────────────────

    async def get_events_organized_by_user(self, user_email: str) -> List[Dict[str, Any]]:
        """
        Non-archived events organized by user.
        Replaces Firestore array_contains on organizers field → indexed JOIN.
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT e.*
                    FROM events e
                    JOIN event_organizers o ON o.event_id = e.event_id
                    WHERE o.user_email = :email AND e.is_archived = FALSE
                    ORDER BY e.start_time ASC NULLS LAST, e.event_id ASC
                """), {"email": user_email})
                return [row_to_event_dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting events organized by {user_email}: {e}", exc_info=True)
            return []

    async def get_events_organized_by_user_paginated(
        self,
        user_email: str,
        cursor_params: Optional[CursorPaginationParams] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        try:
            sql = """
                SELECT e.*
                FROM events e
                JOIN event_organizers o ON o.event_id = e.event_id
                WHERE o.user_email = :email AND e.is_archived = FALSE
                  {cursor_clause}
                ORDER BY e.start_time ASC NULLS LAST, e.event_id ASC
                LIMIT {limit}
            """
            return await self._paginate_user_events(sql, {"email": user_email}, cursor_params)
        except Exception as e:
            self.logger.error(f"Error getting paginated events organized by {user_email}: {e}")
            raise

    # ─── Moderated by user ────────────────────────────────────────────────────

    async def get_events_moderated_by_user(self, user_email: str) -> List[Dict[str, Any]]:
        """
        Non-archived events moderated by user.
        Replaces Firestore array_contains on moderators field → indexed JOIN.
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT e.*
                    FROM events e
                    JOIN event_moderators m ON m.event_id = e.event_id
                    WHERE m.user_email = :email AND e.is_archived = FALSE
                    ORDER BY e.start_time ASC NULLS LAST, e.event_id ASC
                """), {"email": user_email})
                return [row_to_event_dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting events moderated by {user_email}: {e}", exc_info=True)
            return []

    async def get_events_moderated_by_user_paginated(
        self,
        user_email: str,
        cursor_params: Optional[CursorPaginationParams] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        try:
            sql = """
                SELECT e.*
                FROM events e
                JOIN event_moderators m ON m.event_id = e.event_id
                WHERE m.user_email = :email AND e.is_archived = FALSE
                  {cursor_clause}
                ORDER BY e.start_time ASC NULLS LAST, e.event_id ASC
                LIMIT {limit}
            """
            return await self._paginate_user_events(sql, {"email": user_email}, cursor_params)
        except Exception as e:
            self.logger.error(f"Error getting paginated events moderated by {user_email}: {e}")
            raise

    # ─── Roles ────────────────────────────────────────────────────────────────

    async def update_event_roles(self, event_id: str, field: str, emails: List[str]) -> bool:
        """Replace organizers or moderators list. Delegates to event_crud_repository pattern."""
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
            self.logger.error(f"Error updating {field} for event {event_id}: {e}", exc_info=True)
            return False

    # ─── Summary ──────────────────────────────────────────────────────────────

    async def get_user_event_summary(self, user_email: str) -> Dict[str, Any]:
        """
        Counts of events created, organized, and moderated by user.
        Replaces 3 sequential full-collection Firestore queries with a single SQL query.
        """
        try:
            async with AsyncSessionLocal() as session:
                row = await session.execute(text("""
                    SELECT
                        COUNT(*) FILTER (WHERE e.created_by_email = :email)                   AS created_count,
                        COUNT(*) FILTER (WHERE o.user_email = :email AND o.user_email IS NOT NULL) AS organized_count,
                        COUNT(*) FILTER (WHERE m.user_email = :email AND m.user_email IS NOT NULL) AS moderated_count
                    FROM events e
                    LEFT JOIN event_organizers o ON o.event_id = e.event_id AND o.user_email = :email
                    LEFT JOIN event_moderators m ON m.event_id = e.event_id AND m.user_email = :email
                    WHERE e.is_archived = FALSE
                      AND (
                          e.created_by_email = :email
                          OR o.user_email = :email
                          OR m.user_email = :email
                      )
                """), {"email": user_email})
                r = row.fetchone()

            created   = int(r.created_count   or 0)
            organized = int(r.organized_count or 0)
            moderated = int(r.moderated_count or 0)
            return {
                "created_count":   created,
                "organized_count": organized,
                "moderated_count": moderated,
                "total_managed":   created + organized + moderated,
            }
        except Exception as e:
            self.logger.error(f"Error getting event summary for {user_email}: {e}", exc_info=True)
            return {"created_count": 0, "organized_count": 0, "moderated_count": 0, "total_managed": 0}
