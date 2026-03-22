from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.models.pagination import CursorInfo, CursorPaginationParams
from app.repositories.events.event_mapper import parse_datetime, row_to_event_dict
from app.utils.logger import get_repository_logger


class EventArchiveRepository:
    """Repository for event archiving and archive management operations."""

    def __init__(self):
        self.logger = get_repository_logger(__name__)

    async def archive_event(self, event_id: str, archived_by: str, reason: str = "Event archived") -> bool:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    UPDATE events SET
                        is_archived    = TRUE,
                        archived_at    = NOW(),
                        archived_by    = :archived_by,
                        archive_reason = :reason,
                        updated_at     = NOW()
                    WHERE event_id = :eid
                """), {"eid": event_id, "archived_by": archived_by, "reason": reason})
                await session.commit()
                ok = result.rowcount > 0
            if ok:
                self.logger.info(f"Event {event_id} archived by {archived_by}")
            return ok
        except Exception as e:
            self.logger.error(f"Error archiving event {event_id}: {e}", exc_info=True)
            return False

    async def unarchive_event(self, event_id: str) -> bool:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    UPDATE events SET
                        is_archived    = FALSE,
                        unarchived_at  = NOW(),
                        archived_at    = NULL,
                        archived_by    = NULL,
                        archive_reason = NULL,
                        updated_at     = NOW()
                    WHERE event_id = :eid
                """), {"eid": event_id})
                await session.commit()
                ok = result.rowcount > 0
            if ok:
                self.logger.info(f"Event {event_id} unarchived")
            return ok
        except Exception as e:
            self.logger.error(f"Error unarchiving event {event_id}: {e}", exc_info=True)
            return False

    async def archive_events_by_ids(
        self, event_ids: List[str], archived_by: str,
        reason: str = "Automatically archived - event ended"
    ) -> int:
        """
        Archive multiple events in a single UPDATE.
        Replaces N sequential Firestore calls with one SQL statement.
        """
        if not event_ids:
            return 0
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    UPDATE events SET
                        is_archived    = TRUE,
                        archived_at    = NOW(),
                        archived_by    = :archived_by,
                        archive_reason = :reason,
                        updated_at     = NOW()
                    WHERE event_id = ANY(:ids)
                      AND is_archived = FALSE
                """), {"ids": event_ids, "archived_by": archived_by, "reason": reason})
                await session.commit()
                count = result.rowcount
            self.logger.info(f"Archived {count} events")
            return count
        except Exception as e:
            self.logger.error(f"Error bulk archiving events: {e}", exc_info=True)
            return 0

    async def get_archived_events(self, user_email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Archived events sorted by archived_at DESC. Replaces Python sort after Firestore query."""
        try:
            where = "AND created_by_email = :email" if user_email else ""
            params = {"email": user_email} if user_email else {}
            async with AsyncSessionLocal() as session:
                result = await session.execute(text(f"""
                    SELECT * FROM events
                    WHERE is_archived = TRUE {where}
                    ORDER BY archived_at DESC NULLS LAST
                """), params)
                return [row_to_event_dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting archived events: {e}", exc_info=True)
            return []

    async def get_archived_events_paginated(
        self,
        cursor_params: Optional[CursorPaginationParams] = None,
        user_email: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Keyset cursor pagination over archived events ordered by archived_at DESC."""
        try:
            page_size = cursor_params.page_size if cursor_params else 20
            params: Dict[str, Any] = {"limit": page_size + 1}
            user_clause = "AND created_by_email = :email" if user_email else ""
            if user_email:
                params["email"] = user_email

            cursor_clause = ""
            if cursor_params and cursor_params.cursor:
                cursor_info = CursorInfo.decode(cursor_params.cursor)
                if cursor_info and cursor_info.start_time:
                    # Paginating DESC: events with archived_at < cursor (older)
                    cursor_clause = """
                        AND (archived_at < :cursor_time
                             OR (archived_at = :cursor_time AND event_id > :cursor_id))
                    """
                    params["cursor_time"] = parse_datetime(cursor_info.start_time)
                    params["cursor_id"] = cursor_info.event_id

            async with AsyncSessionLocal() as session:
                result = await session.execute(text(f"""
                    SELECT * FROM events
                    WHERE is_archived = TRUE
                      {user_clause}
                      {cursor_clause}
                    ORDER BY archived_at DESC NULLS LAST, event_id ASC
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
                    start_time=last.get("archivedAt"),
                    event_id=last.get("eventId")
                ).encode()

            self.logger.info(f"Retrieved {len(events)} archived events (has_next: {has_next})")
            return events, next_cursor
        except Exception as e:
            self.logger.error(f"Error getting paginated archived events: {e}")
            raise

    async def get_archive_statistics(self) -> Dict[str, Any]:
        """
        Archive stats via SQL aggregation.
        Replaces loading all archived docs into Python for counting.
        """
        try:
            async with AsyncSessionLocal() as session:
                total = await session.scalar(
                    text("SELECT COUNT(*) FROM events WHERE is_archived = TRUE")
                )
                result = await session.execute(text("""
                    SELECT TO_CHAR(archived_at, 'YYYY-MM') AS month, COUNT(*) AS cnt
                    FROM events
                    WHERE is_archived = TRUE AND archived_at IS NOT NULL
                    GROUP BY month
                    ORDER BY month DESC
                    LIMIT 12
                """))
                monthly = {row.month: row.cnt for row in result.fetchall()}

            return {"total_archived": total, "monthly_archived": monthly}
        except Exception as e:
            self.logger.error(f"Error getting archive statistics: {e}", exc_info=True)
            return {"total_archived": 0, "monthly_archived": {}}
