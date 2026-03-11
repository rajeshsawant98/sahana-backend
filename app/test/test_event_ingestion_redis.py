"""
Tests for Redis integration in app/services/event_ingestion_service.py

Covers:
- ingest_event: Redis dedup (hit / miss / failure fallback)
- ingest_events_for_all_cities: mutex lock acquisition / contention / finally release
- _fetch_tm_all_cities: Ticketmaster API cache hit / miss
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── ingest_event ─────────────────────────────────────────────────────────────

class TestIngestEvent:

    @pytest.mark.asyncio
    async def test_no_original_id_saves_directly_without_redis(self):
        from app.services.event_ingestion_service import ingest_event, repo
        with patch.object(repo, 'save_event', new_callable=AsyncMock, return_value=True) as mock_save:
            result = await ingest_event({"title": "No-ID Event"}, redis=None)
        assert result is True
        mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_dedup_hit_returns_false_without_firestore(self):
        from app.services.event_ingestion_service import ingest_event, repo
        mock_redis = AsyncMock()
        mock_redis.sismember = AsyncMock(return_value=1)  # already in SET
        with patch.object(repo, 'get_by_original_id', new_callable=AsyncMock) as mock_db:
            result = await ingest_event({"originalId": "tm-001"}, redis=mock_redis)
        assert result is False
        mock_redis.sismember.assert_called_once()
        mock_db.assert_not_called()  # Firestore never queried

    @pytest.mark.asyncio
    async def test_redis_miss_firestore_hit_returns_false(self):
        from app.services.event_ingestion_service import ingest_event, repo
        mock_redis = AsyncMock()
        mock_redis.sismember = AsyncMock(return_value=0)
        with patch.object(repo, 'get_by_original_id', new_callable=AsyncMock, return_value={"id": "existing"}):
            result = await ingest_event({"originalId": "tm-002"}, redis=mock_redis)
        assert result is False

    @pytest.mark.asyncio
    async def test_redis_miss_firestore_miss_saves_and_adds_to_redis(self):
        from app.services.event_ingestion_service import ingest_event, repo
        mock_redis = AsyncMock()
        mock_redis.sismember = AsyncMock(return_value=0)
        mock_redis.sadd = AsyncMock()
        mock_redis.expire = AsyncMock()
        with patch.object(repo, 'get_by_original_id', new_callable=AsyncMock, return_value=None):
            with patch.object(repo, 'save_event', new_callable=AsyncMock, return_value=True):
                result = await ingest_event({"originalId": "tm-003"}, redis=mock_redis)
        assert result is True
        mock_redis.sadd.assert_called_once()
        mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_sadd_not_called_when_save_returns_false(self):
        from app.services.event_ingestion_service import ingest_event, repo
        mock_redis = AsyncMock()
        mock_redis.sismember = AsyncMock(return_value=0)
        mock_redis.sadd = AsyncMock()
        with patch.object(repo, 'get_by_original_id', new_callable=AsyncMock, return_value=None):
            with patch.object(repo, 'save_event', new_callable=AsyncMock, return_value=False):
                result = await ingest_event({"originalId": "tm-004"}, redis=mock_redis)
        assert result is False
        mock_redis.sadd.assert_not_called()

    @pytest.mark.asyncio
    async def test_redis_sismember_failure_falls_back_to_firestore(self):
        from app.services.event_ingestion_service import ingest_event, repo
        mock_redis = AsyncMock()
        mock_redis.sismember = AsyncMock(side_effect=Exception("Redis timeout"))
        with patch.object(repo, 'get_by_original_id', new_callable=AsyncMock, return_value=None):
            with patch.object(repo, 'save_event', new_callable=AsyncMock, return_value=True):
                result = await ingest_event({"originalId": "tm-005"}, redis=mock_redis)
        assert result is True  # fell back to Firestore path and saved

    @pytest.mark.asyncio
    async def test_no_redis_uses_firestore_dedup(self):
        from app.services.event_ingestion_service import ingest_event, repo
        with patch.object(repo, 'get_by_original_id', new_callable=AsyncMock, return_value={"id": "exists"}):
            result = await ingest_event({"originalId": "tm-006"}, redis=None)
        assert result is False


# ── Mutex lock ────────────────────────────────────────────────────────────────

class TestIngestionMutex:

    @pytest.mark.asyncio
    async def test_lock_not_acquired_returns_skipped(self):
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=None)  # NX set failed — lock already held

        with patch('app.services.event_ingestion_service.get_redis_client', return_value=mock_redis):
            from app.services.event_ingestion_service import ingest_events_for_all_cities
            result = await ingest_events_for_all_cities()

        assert result["status"] == "skipped"
        assert result["reason"] == "ingestion_locked"

    @pytest.mark.asyncio
    async def test_lock_released_in_finally_on_exception(self):
        """Lock must be deleted even when an exception occurs during ingestion."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock()

        async def _raise(*args, **kwargs):
            raise RuntimeError("Firestore unavailable")

        with patch('app.services.event_ingestion_service.get_redis_client', return_value=mock_redis):
            with patch('app.services.event_ingestion_service.load_url_cache', new_callable=AsyncMock, return_value=set()):
                with patch('app.services.event_ingestion_service.get_unique_user_locations', side_effect=_raise):
                    from app.services.event_ingestion_service import ingest_events_for_all_cities
                    with pytest.raises(RuntimeError):
                        await ingest_events_for_all_cities()

        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_lock_released_after_successful_run(self):
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock()

        async def _noop_flush():
            pass

        with patch('app.services.event_ingestion_service.get_redis_client', return_value=mock_redis):
            with patch('app.services.event_ingestion_service.load_url_cache', new_callable=AsyncMock, return_value=set()):
                with patch('app.services.event_ingestion_service.get_unique_user_locations', new_callable=AsyncMock, return_value=[]):
                    with patch('app.services.event_ingestion_service._fetch_tm_all_cities', new_callable=AsyncMock, return_value={}):
                        with patch('app.services.event_ingestion_service.save_url_cache', new_callable=AsyncMock):
                            with patch('app.services.event_ingestion_service._flush_event_query_cache', new=lambda: _noop_flush()):
                                from app.services.event_ingestion_service import ingest_events_for_all_cities
                                result = await ingest_events_for_all_cities()

        assert result["status"] == "success"
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_redis_runs_without_lock(self):
        """When Redis is unavailable the ingestion still runs — no lock, no crash."""
        async def _noop_flush():
            pass

        with patch('app.services.event_ingestion_service.get_redis_client', return_value=None):
            with patch('app.services.event_ingestion_service.load_url_cache', new_callable=AsyncMock, return_value=set()):
                with patch('app.services.event_ingestion_service.get_unique_user_locations', new_callable=AsyncMock, return_value=[]):
                    with patch('app.services.event_ingestion_service._fetch_tm_all_cities', new_callable=AsyncMock, return_value={}):
                        with patch('app.services.event_ingestion_service.save_url_cache', new_callable=AsyncMock):
                            with patch('app.services.event_ingestion_service._flush_event_query_cache', new=lambda: _noop_flush()):
                                from app.services.event_ingestion_service import ingest_events_for_all_cities
                                result = await ingest_events_for_all_cities()

        assert result["status"] == "success"


# ── Ticketmaster API cache ────────────────────────────────────────────────────

class TestTicketmasterCache:

    @pytest.mark.asyncio
    async def test_cache_hit_skips_api_call(self):
        from app.services.event_ingestion_service import _fetch_tm_all_cities
        cached_events = [{"title": "Cached Event", "startTime": "2026-06-01T20:00:00"}]
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_events))

        with patch('app.services.event_ingestion_service.fetch_ticketmaster_events') as mock_api:
            result = await _fetch_tm_all_cities([("Austin", "TX")], redis=mock_redis)

        assert result["Austin,TX"] == cached_events
        mock_api.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_calls_api_and_stores_result(self):
        from app.services.event_ingestion_service import _fetch_tm_all_cities
        api_events = [{"title": "Live Event", "startTime": "2026-06-01T20:00:00"}]
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        with patch('app.services.event_ingestion_service.fetch_ticketmaster_events', return_value=api_events):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await _fetch_tm_all_cities([("Austin", "TX")], redis=mock_redis)

        assert result["Austin,TX"] == api_events
        mock_redis.set.assert_called_once()
        # Verify the stored value is the JSON-encoded events
        stored_json = mock_redis.set.call_args[0][1]
        assert json.loads(stored_json) == api_events

    @pytest.mark.asyncio
    async def test_cache_miss_sleeps_for_rate_limit(self):
        from app.services.event_ingestion_service import _fetch_tm_all_cities
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        with patch('app.services.event_ingestion_service.fetch_ticketmaster_events', return_value=[]):
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                await _fetch_tm_all_cities([("Austin", "TX")], redis=mock_redis)

        mock_sleep.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_cache_hit_skips_sleep(self):
        from app.services.event_ingestion_service import _fetch_tm_all_cities
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps([]))

        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await _fetch_tm_all_cities([("Austin", "TX")], redis=mock_redis)

        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_redis_always_calls_api(self):
        from app.services.event_ingestion_service import _fetch_tm_all_cities
        api_events = [{"title": "Event"}]

        with patch('app.services.event_ingestion_service.fetch_ticketmaster_events', return_value=api_events) as mock_api:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await _fetch_tm_all_cities([("Austin", "TX"), ("Denver", "CO")], redis=None)

        assert mock_api.call_count == 2

    @pytest.mark.asyncio
    async def test_api_error_returns_empty_list_for_city(self):
        from app.services.event_ingestion_service import _fetch_tm_all_cities
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        with patch('app.services.event_ingestion_service.fetch_ticketmaster_events', side_effect=Exception("API error")):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await _fetch_tm_all_cities([("Austin", "TX")], redis=mock_redis)

        assert result["Austin,TX"] == []
