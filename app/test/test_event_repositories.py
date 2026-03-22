"""
Unit tests for event repositories:
- EventRsvpRepository
- EventArchiveRepository
- EventIngestionRepository
- EventUserRepository

All DB interactions are mocked — no real PostgreSQL connection.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.asyncio


# ─── Mock session factory ──────────────────────────────────────────────────────

def make_mock_session():
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    return session


def _make_execute_result(rowcount=1, fetchone_row=None, fetchall_rows=None):
    mock_result = MagicMock()
    mock_result.rowcount = rowcount
    mock_result.fetchone.return_value = fetchone_row
    mock_result.fetchall.return_value = fetchall_rows or []
    return mock_result


def _make_row(mapping: dict):
    row = MagicMock()
    row._mapping = mapping
    return row


# ═══════════════════════════════════════════════════════════════════════════════
# EventRsvpRepository
# ═══════════════════════════════════════════════════════════════════════════════

_RSVP_PATCH = 'app.repositories.events.event_rsvp_repository.AsyncSessionLocal'


class TestEventRsvpRepository:

    async def test_join_rsvp_calls_set_rsvp_status_with_joined(self):
        from app.repositories.events.event_rsvp_repository import EventRsvpRepository
        repo = EventRsvpRepository()
        called_with = {}

        async def mock_set_status(event_id, user_email, status):
            called_with["status"] = status
            return True

        repo._set_rsvp_status = mock_set_status
        result = await repo.join_rsvp("evt-001", "user@example.com")
        assert called_with["status"] == "joined"
        assert result is True

    async def test_set_rsvp_status_returns_false_when_event_not_found(self):
        from app.repositories.events.event_rsvp_repository import EventRsvpRepository
        session = make_mock_session()
        # scalar returns None → event doesn't exist
        session.scalar = AsyncMock(return_value=None)

        with patch(_RSVP_PATCH, return_value=session):
            repo = EventRsvpRepository()
            result = await repo._set_rsvp_status("no-such-event", "user@example.com", "joined")

        assert result is False
        # execute (the INSERT) should NOT be called when event doesn't exist
        session.execute.assert_not_called()

    async def test_set_rsvp_status_returns_true_when_event_exists(self):
        from app.repositories.events.event_rsvp_repository import EventRsvpRepository
        session = make_mock_session()
        # scalar returns 1 → event exists
        session.scalar = AsyncMock(return_value=1)
        session.execute = AsyncMock(return_value=MagicMock())

        with patch(_RSVP_PATCH, return_value=session):
            repo = EventRsvpRepository()
            result = await repo._set_rsvp_status("evt-001", "user@example.com", "joined")

        assert result is True
        session.execute.assert_called_once()
        session.commit.assert_called_once()

    async def test_cancel_rsvp_returns_true_on_success(self):
        from app.repositories.events.event_rsvp_repository import EventRsvpRepository
        session = make_mock_session()
        session.execute = AsyncMock(return_value=_make_execute_result(rowcount=1))

        with patch(_RSVP_PATCH, return_value=session):
            repo = EventRsvpRepository()
            result = await repo.cancel_rsvp("evt-001", "user@example.com")

        assert result is True

    async def test_update_rsvp_status_non_attended_sets_rating_and_review_to_none(self):
        """When status != 'attended', rating and review must be None in the SQL params."""
        from app.repositories.events.event_rsvp_repository import EventRsvpRepository
        session = make_mock_session()
        mock_result = _make_execute_result(rowcount=1)
        captured_params = {}

        async def capture_execute(query, params=None):
            if params:
                captured_params.update(params)
            return mock_result

        session.execute = capture_execute

        with patch(_RSVP_PATCH, return_value=session):
            repo = EventRsvpRepository()
            result = await repo.update_rsvp_status(
                "evt-001", "user@example.com",
                status="joined",
                rating=5,
                review="Great event"
            )

        assert result is True
        assert captured_params["rating"] is None
        assert captured_params["review"] is None

    async def test_update_rsvp_status_attended_keeps_rating_and_review(self):
        from app.repositories.events.event_rsvp_repository import EventRsvpRepository
        session = make_mock_session()
        mock_result = _make_execute_result(rowcount=1)
        captured_params = {}

        async def capture_execute(query, params=None):
            if params:
                captured_params.update(params)
            return mock_result

        session.execute = capture_execute

        with patch(_RSVP_PATCH, return_value=session):
            repo = EventRsvpRepository()
            await repo.update_rsvp_status(
                "evt-001", "user@example.com",
                status="attended",
                rating=4,
                review="Was good"
            )

        assert captured_params["rating"] == 4
        assert captured_params["review"] == "Was good"


# ═══════════════════════════════════════════════════════════════════════════════
# EventArchiveRepository
# ═══════════════════════════════════════════════════════════════════════════════

_ARCHIVE_PATCH = 'app.repositories.events.event_archive_repository.AsyncSessionLocal'


class TestEventArchiveRepository:

    async def test_archive_event_returns_true_when_rowcount_gt_0(self):
        from app.repositories.events.event_archive_repository import EventArchiveRepository
        session = make_mock_session()
        session.execute = AsyncMock(return_value=_make_execute_result(rowcount=1))

        with patch(_ARCHIVE_PATCH, return_value=session):
            repo = EventArchiveRepository()
            result = await repo.archive_event("evt-001", "admin@example.com")

        assert result is True

    async def test_archive_event_returns_false_when_rowcount_is_0(self):
        from app.repositories.events.event_archive_repository import EventArchiveRepository
        session = make_mock_session()
        session.execute = AsyncMock(return_value=_make_execute_result(rowcount=0))

        with patch(_ARCHIVE_PATCH, return_value=session):
            repo = EventArchiveRepository()
            result = await repo.archive_event("no-such-event", "admin@example.com")

        assert result is False

    async def test_archive_events_by_ids_returns_0_for_empty_list(self):
        from app.repositories.events.event_archive_repository import EventArchiveRepository
        session = make_mock_session()

        with patch(_ARCHIVE_PATCH, return_value=session):
            repo = EventArchiveRepository()
            result = await repo.archive_events_by_ids([], "admin@example.com")

        assert result == 0
        session.execute.assert_not_called()

    async def test_archive_events_by_ids_returns_rowcount(self):
        from app.repositories.events.event_archive_repository import EventArchiveRepository
        session = make_mock_session()
        session.execute = AsyncMock(return_value=_make_execute_result(rowcount=3))

        with patch(_ARCHIVE_PATCH, return_value=session):
            repo = EventArchiveRepository()
            result = await repo.archive_events_by_ids(
                ["evt-001", "evt-002", "evt-003"], "admin@example.com"
            )

        assert result == 3

    async def test_unarchive_event_sets_is_archived_false(self):
        from app.repositories.events.event_archive_repository import EventArchiveRepository
        session = make_mock_session()
        mock_result = _make_execute_result(rowcount=1)
        captured_sql = []

        async def capture_execute(query, params=None):
            captured_sql.append(str(query))
            return mock_result

        session.execute = capture_execute

        with patch(_ARCHIVE_PATCH, return_value=session):
            repo = EventArchiveRepository()
            result = await repo.unarchive_event("evt-001")

        assert result is True
        assert any("FALSE" in sql or "is_archived" in sql.lower() for sql in captured_sql)

    async def test_unarchive_event_returns_false_when_not_found(self):
        from app.repositories.events.event_archive_repository import EventArchiveRepository
        session = make_mock_session()
        session.execute = AsyncMock(return_value=_make_execute_result(rowcount=0))

        with patch(_ARCHIVE_PATCH, return_value=session):
            repo = EventArchiveRepository()
            result = await repo.unarchive_event("no-such-event")

        assert result is False


# ═══════════════════════════════════════════════════════════════════════════════
# EventIngestionRepository
# ═══════════════════════════════════════════════════════════════════════════════

_INGESTION_PATCH = 'app.repositories.events.event_ingestion_repository.AsyncSessionLocal'


class TestEventIngestionRepository:

    def _sample_event(self):
        return {
            "eventId": "evt-ingest-001",
            "eventName": "Test Ingested Event",
            "description": "A test event",
            "location": {
                "city": "Austin",
                "state": "TX",
                "country": "US",
                "latitude": 30.26,
                "longitude": -97.74,
            },
            "startTime": "2025-08-01T20:00:00Z",
            "categories": ["music"],
            "isOnline": False,
            "createdBy": "Ingester",
            "createdByEmail": "ingester@example.com",
            "origin": "external",
            "source": "ticketmaster",
            "originalId": "tm-12345",
        }

    async def test_save_event_returns_true_on_success(self):
        from app.repositories.events.event_ingestion_repository import EventIngestionRepository
        session = make_mock_session()
        session.execute = AsyncMock(return_value=MagicMock())

        with patch(_INGESTION_PATCH, return_value=session):
            repo = EventIngestionRepository()
            result = await repo.save_event(self._sample_event())

        assert result is True
        session.commit.assert_called_once()

    async def test_save_event_returns_false_on_exception(self):
        from app.repositories.events.event_ingestion_repository import EventIngestionRepository
        session = make_mock_session()
        session.execute = AsyncMock(side_effect=Exception("DB connection error"))

        with patch(_INGESTION_PATCH, return_value=session):
            repo = EventIngestionRepository()
            result = await repo.save_event(self._sample_event())

        assert result is False

    async def test_get_by_original_id_returns_none_when_no_row(self):
        from app.repositories.events.event_ingestion_repository import EventIngestionRepository
        session = make_mock_session()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        with patch(_INGESTION_PATCH, return_value=session):
            repo = EventIngestionRepository()
            result = await repo.get_by_original_id("tm-not-found")

        assert result is None

    async def test_get_by_original_id_returns_dict_with_event_id(self):
        from app.repositories.events.event_ingestion_repository import EventIngestionRepository
        session = make_mock_session()
        row = MagicMock()
        row.event_id = "evt-001"
        mock_result = MagicMock()
        mock_result.fetchone.return_value = row
        session.execute = AsyncMock(return_value=mock_result)

        with patch(_INGESTION_PATCH, return_value=session):
            repo = EventIngestionRepository()
            result = await repo.get_by_original_id("tm-12345")

        assert result == {"event_id": "evt-001"}


# ═══════════════════════════════════════════════════════════════════════════════
# EventUserRepository
# ═══════════════════════════════════════════════════════════════════════════════

_USER_REPO_PATCH = 'app.repositories.events.event_user_repository.AsyncSessionLocal'


class TestEventUserRepository:

    async def test_get_user_event_summary_returns_correct_counts(self):
        from app.repositories.events.event_user_repository import EventUserRepository
        session = make_mock_session()

        summary_row = MagicMock()
        summary_row.created_count = 5
        summary_row.organized_count = 3
        summary_row.moderated_count = 2

        mock_result = MagicMock()
        mock_result.fetchone.return_value = summary_row
        session.execute = AsyncMock(return_value=mock_result)

        with patch(_USER_REPO_PATCH, return_value=session):
            repo = EventUserRepository()
            result = await repo.get_user_event_summary("user@example.com")

        assert result["created_count"] == 5
        assert result["organized_count"] == 3
        assert result["moderated_count"] == 2
        assert result["total_managed"] == 10

    async def test_get_user_event_summary_handles_none_counts(self):
        """None values from SQL aggregation (no rows) should default to 0."""
        from app.repositories.events.event_user_repository import EventUserRepository
        session = make_mock_session()

        summary_row = MagicMock()
        summary_row.created_count = None
        summary_row.organized_count = None
        summary_row.moderated_count = None

        mock_result = MagicMock()
        mock_result.fetchone.return_value = summary_row
        session.execute = AsyncMock(return_value=mock_result)

        with patch(_USER_REPO_PATCH, return_value=session):
            repo = EventUserRepository()
            result = await repo.get_user_event_summary("user@example.com")

        assert result["created_count"] == 0
        assert result["total_managed"] == 0

    async def test_update_event_roles_calls_delete_then_insert(self):
        from app.repositories.events.event_user_repository import EventUserRepository
        session = make_mock_session()
        execute_calls = []

        async def capture_execute(query, params=None):
            execute_calls.append((str(query), params))
            return MagicMock()

        session.execute = capture_execute

        with patch(_USER_REPO_PATCH, return_value=session):
            repo = EventUserRepository()
            result = await repo.update_event_roles(
                "evt-001",
                "organizers",
                ["alice@example.com", "bob@example.com"]
            )

        assert result is True
        session.commit.assert_called_once()
        # First call should be DELETE
        assert len(execute_calls) >= 3  # 1 DELETE + 2 INSERTs
        first_sql = execute_calls[0][0].upper()
        assert "DELETE" in first_sql

    async def test_update_event_roles_uses_correct_table_for_organizers(self):
        from app.repositories.events.event_user_repository import EventUserRepository
        session = make_mock_session()
        execute_calls = []

        async def capture_execute(query, params=None):
            execute_calls.append(str(query))
            return MagicMock()

        session.execute = capture_execute

        with patch(_USER_REPO_PATCH, return_value=session):
            repo = EventUserRepository()
            await repo.update_event_roles("evt-001", "organizers", ["a@example.com"])

        all_sql = " ".join(execute_calls)
        assert "event_organizers" in all_sql

    async def test_update_event_roles_uses_correct_table_for_moderators(self):
        from app.repositories.events.event_user_repository import EventUserRepository
        session = make_mock_session()
        execute_calls = []

        async def capture_execute(query, params=None):
            execute_calls.append(str(query))
            return MagicMock()

        session.execute = capture_execute

        with patch(_USER_REPO_PATCH, return_value=session):
            repo = EventUserRepository()
            await repo.update_event_roles("evt-001", "moderators", ["a@example.com"])

        all_sql = " ".join(execute_calls)
        assert "event_moderators" in all_sql

    async def test_update_event_roles_returns_true_on_success(self):
        from app.repositories.events.event_user_repository import EventUserRepository
        session = make_mock_session()
        session.execute = AsyncMock(return_value=MagicMock())

        with patch(_USER_REPO_PATCH, return_value=session):
            repo = EventUserRepository()
            result = await repo.update_event_roles("evt-001", "organizers", [])

        assert result is True
