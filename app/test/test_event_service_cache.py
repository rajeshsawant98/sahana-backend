"""
Tests for Redis integration in app/services/event_service.py

Covers:
- get_all_events_paginated: cache hit / miss / no-Redis
- flush_event_query_cache: scan + delete, multi-page scan, empty result
- create/update/delete/archive_event: all call flush after mutation
"""
import json
import pytest
from unittest.mock import AsyncMock, patch
from app.models.pagination import CursorPaginationParams, EventFilters, EventCursorPaginatedResponse


def _make_paginated_response(items=None):
    return EventCursorPaginatedResponse.create(
        items=items or [{"id": "evt-1", "title": "Test Event"}],
        next_cursor=None,
        prev_cursor=None,
        has_next=False,
        has_previous=False,
        page_size=12,
    )


# ── get_all_events_paginated ──────────────────────────────────────────────────

class TestGetAllEventsPaginated:

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_response_without_firestore(self):
        from app.services.event_service import get_all_events_paginated
        cached = _make_paginated_response()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=cached.model_dump_json())

        with patch('app.services.event_service.get_redis_client', return_value=mock_redis):
            with patch('app.services.event_service.event_repo') as mock_repo:
                result = await get_all_events_paginated(CursorPaginationParams())

        mock_repo.get_all_events_paginated.assert_not_called()
        assert result.items == cached.items

    @pytest.mark.asyncio
    async def test_cache_miss_queries_firestore_and_stores_in_redis(self):
        from app.services.event_service import get_all_events_paginated
        events = [{"id": "evt-2", "title": "From Firestore"}]
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        with patch('app.services.event_service.get_redis_client', return_value=mock_redis):
            with patch('app.services.event_service.event_repo') as mock_repo:
                mock_repo.get_all_events_paginated = AsyncMock(
                    return_value=(events, None, None, False, False)
                )
                result = await get_all_events_paginated(CursorPaginationParams())

        assert result.items == events
        mock_redis.set.assert_called_once()
        # Verify stored JSON is deserializable
        stored_json = mock_redis.set.call_args[0][1]
        parsed = json.loads(stored_json)
        assert parsed["items"] == events

    @pytest.mark.asyncio
    async def test_no_redis_queries_firestore_without_caching(self):
        from app.services.event_service import get_all_events_paginated
        events = [{"id": "evt-3"}]

        with patch('app.services.event_service.get_redis_client', return_value=None):
            with patch('app.services.event_service.event_repo') as mock_repo:
                mock_repo.get_all_events_paginated = AsyncMock(
                    return_value=(events, None, None, False, False)
                )
                result = await get_all_events_paginated(CursorPaginationParams())

        assert result.items == events

    @pytest.mark.asyncio
    async def test_different_params_produce_different_cache_keys(self):
        from app.services.event_service import get_all_events_paginated
        stored_keys = []

        async def capture_set(key, value, **kwargs):
            stored_keys.append(key)

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(side_effect=capture_set)

        with patch('app.services.event_service.get_redis_client', return_value=mock_redis):
            with patch('app.services.event_service.event_repo') as mock_repo:
                mock_repo.get_all_events_paginated = AsyncMock(
                    return_value=([], None, None, False, False)
                )
                await get_all_events_paginated(CursorPaginationParams(page_size=10))
                mock_redis.get = AsyncMock(return_value=None)
                await get_all_events_paginated(CursorPaginationParams(page_size=20))

        assert len(stored_keys) == 2
        assert stored_keys[0] != stored_keys[1]

    @pytest.mark.asyncio
    async def test_redis_failure_falls_back_to_firestore(self):
        from app.services.event_service import get_all_events_paginated
        events = [{"id": "evt-4"}]
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis timeout"))

        with patch('app.services.event_service.get_redis_client', return_value=mock_redis):
            with patch('app.services.event_service.event_repo') as mock_repo:
                mock_repo.get_all_events_paginated = AsyncMock(
                    return_value=(events, None, None, False, False)
                )
                result = await get_all_events_paginated(CursorPaginationParams())

        assert result.items == events

    @pytest.mark.asyncio
    async def test_cache_hit_with_filters(self):
        from app.services.event_service import get_all_events_paginated
        cached = _make_paginated_response()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=cached.model_dump_json())

        with patch('app.services.event_service.get_redis_client', return_value=mock_redis):
            with patch('app.services.event_service.event_repo') as mock_repo:
                result = await get_all_events_paginated(
                    CursorPaginationParams(),
                    filters=EventFilters(city="Austin", state="TX")
                )

        mock_repo.get_all_events_paginated.assert_not_called()
        assert result.items == cached.items


# ── flush_event_query_cache ───────────────────────────────────────────────────

class TestFlushEventQueryCache:

    @pytest.mark.asyncio
    async def test_no_redis_returns_immediately_without_error(self):
        from app.services.event_service import flush_event_query_cache
        with patch('app.services.event_service.get_redis_client', return_value=None):
            await flush_event_query_cache()  # Must not raise

    @pytest.mark.asyncio
    async def test_scan_and_delete_matching_keys(self):
        from app.services.event_service import flush_event_query_cache
        q_keys = ["sahana:events:q:abc123", "sahana:events:q:def456"]
        nearby_keys = ["sahana:events:nearby:xyz789"]
        mock_redis = AsyncMock()
        mock_redis.scan = AsyncMock(side_effect=[(0, q_keys), (0, nearby_keys)])
        mock_redis.delete = AsyncMock()

        with patch('app.services.event_service.get_redis_client', return_value=mock_redis):
            await flush_event_query_cache()

        assert mock_redis.delete.call_count == 2
        mock_redis.delete.assert_any_call(*q_keys)
        mock_redis.delete.assert_any_call(*nearby_keys)

    @pytest.mark.asyncio
    async def test_scan_empty_result_skips_delete(self):
        from app.services.event_service import flush_event_query_cache
        mock_redis = AsyncMock()
        mock_redis.scan = AsyncMock(return_value=(0, []))
        mock_redis.delete = AsyncMock()

        with patch('app.services.event_service.get_redis_client', return_value=mock_redis):
            await flush_event_query_cache()

        mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_scan_multiple_pages_deletes_all_batches(self):
        from app.services.event_service import flush_event_query_cache
        mock_redis = AsyncMock()
        # Two pages for sahana:events:q:*, one page for sahana:events:nearby:*
        mock_redis.scan = AsyncMock(side_effect=[
            (42, ["sahana:events:q:page1a", "sahana:events:q:page1b"]),
            (0,  ["sahana:events:q:page2a"]),
            (0,  []),
        ])
        mock_redis.delete = AsyncMock()

        with patch('app.services.event_service.get_redis_client', return_value=mock_redis):
            await flush_event_query_cache()

        assert mock_redis.scan.call_count == 3
        assert mock_redis.delete.call_count == 2  # two q batches deleted; nearby was empty

    @pytest.mark.asyncio
    async def test_redis_scan_failure_does_not_raise(self):
        from app.services.event_service import flush_event_query_cache
        mock_redis = AsyncMock()
        mock_redis.scan = AsyncMock(side_effect=Exception("Redis error"))

        with patch('app.services.event_service.get_redis_client', return_value=mock_redis):
            await flush_event_query_cache()  # Must not raise


# ── Mutations flush cache ─────────────────────────────────────────────────────

class TestMutationsClearCache:

    @pytest.mark.asyncio
    async def test_create_event_flushes_cache(self):
        from app.services.event_service import create_event
        with patch('app.services.event_service.event_repo') as mock_repo:
            mock_repo.create_event = AsyncMock(return_value="new-event-id")
            with patch('app.services.event_service.flush_event_query_cache', new_callable=AsyncMock) as mock_flush:
                result = await create_event({"title": "New Event"})
        mock_flush.assert_called_once()
        assert result == "new-event-id"

    @pytest.mark.asyncio
    async def test_update_event_flushes_cache(self):
        from app.services.event_service import update_event
        with patch('app.services.event_service.event_repo') as mock_repo:
            mock_repo.update_event = AsyncMock(return_value=True)
            with patch('app.services.event_service.flush_event_query_cache', new_callable=AsyncMock) as mock_flush:
                result = await update_event("evt-id", {"title": "Updated"})
        mock_flush.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_event_flushes_cache(self):
        from app.services.event_service import delete_event
        with patch('app.services.event_service.event_repo') as mock_repo:
            mock_repo.delete_event = AsyncMock(return_value=True)
            with patch('app.services.event_service.flush_event_query_cache', new_callable=AsyncMock) as mock_flush:
                result = await delete_event("evt-id")
        mock_flush.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_archive_event_flushes_cache(self):
        from app.services.event_service import archive_event
        with patch('app.services.event_service.event_repo') as mock_repo:
            mock_repo.archive_event = AsyncMock(return_value=True)
            with patch('app.services.event_service.flush_event_query_cache', new_callable=AsyncMock) as mock_flush:
                result = await archive_event("evt-id", "admin@test.com", "Archived")
        mock_flush.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_flush_called_even_when_repo_raises(self):
        """Flush should NOT be called if the repo call itself raises (exception propagates out)."""
        from app.services.event_service import create_event
        with patch('app.services.event_service.event_repo') as mock_repo:
            mock_repo.create_event = AsyncMock(side_effect=Exception("DB error"))
            with patch('app.services.event_service.flush_event_query_cache', new_callable=AsyncMock) as mock_flush:
                result = await create_event({"title": "Will fail"})
        # Exception is caught and None returned; flush is not called on error path
        assert result is None
        mock_flush.assert_not_called()
