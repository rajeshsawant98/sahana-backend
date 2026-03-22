"""
Unit tests for app/utils/location_utils.py

Tests get_unique_user_locations with mocked Redis and DB session.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.asyncio


# ─── Mock session factory ──────────────────────────────────────────────────────

def make_mock_session():
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    return session


def _make_location_row(city: str, state: str):
    row = MagicMock()
    row.city = city
    row.state = state
    return row


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestGetUniqueUserLocations:

    async def test_redis_cache_hit_returns_cached_list_without_db(self):
        from app.utils.location_utils import get_unique_user_locations

        cached_data = [["Austin", "TX"], ["Denver", "CO"]]
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_data))

        session = make_mock_session()

        with patch('app.utils.location_utils.AsyncSessionLocal', return_value=session):
            result = await get_unique_user_locations(redis=mock_redis)

        assert result == [("Austin", "TX"), ("Denver", "CO")]
        # DB must not be called
        session.execute.assert_not_called()
        mock_redis.get.assert_called_once()

    async def test_redis_miss_queries_db_and_returns_locations(self):
        from app.utils.location_utils import get_unique_user_locations

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)  # cache miss
        mock_redis.set = AsyncMock()

        session = make_mock_session()
        db_rows = [
            _make_location_row("Austin", "TX"),
            _make_location_row("Denver", "CO"),
        ]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = db_rows
        session.execute = AsyncMock(return_value=mock_result)

        with patch('app.utils.location_utils.AsyncSessionLocal', return_value=session):
            result = await get_unique_user_locations(redis=mock_redis)

        assert ("Austin", "TX") in result
        assert ("Denver", "CO") in result
        assert len(result) == 2

    async def test_redis_miss_stores_result_in_cache(self):
        from app.utils.location_utils import get_unique_user_locations

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        session = make_mock_session()
        db_rows = [_make_location_row("Austin", "TX")]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = db_rows
        session.execute = AsyncMock(return_value=mock_result)

        with patch('app.utils.location_utils.AsyncSessionLocal', return_value=session):
            await get_unique_user_locations(redis=mock_redis)

        mock_redis.set.assert_called_once()
        # Verify stored value is valid JSON
        stored_json = mock_redis.set.call_args[0][1]
        stored = json.loads(stored_json)
        assert stored == [["Austin", "TX"]]

    async def test_redis_unavailable_falls_through_to_db(self):
        from app.utils.location_utils import get_unique_user_locations

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis connection refused"))

        session = make_mock_session()
        db_rows = [_make_location_row("Seattle", "WA")]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = db_rows
        session.execute = AsyncMock(return_value=mock_result)

        with patch('app.utils.location_utils.AsyncSessionLocal', return_value=session):
            result = await get_unique_user_locations(redis=mock_redis)

        # Should still return results from DB despite Redis failure
        assert result == [("Seattle", "WA")]

    async def test_empty_db_result_returns_empty_list(self):
        from app.utils.location_utils import get_unique_user_locations

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        session = make_mock_session()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with patch('app.utils.location_utils.AsyncSessionLocal', return_value=session):
            result = await get_unique_user_locations(redis=mock_redis)

        assert result == []

    async def test_no_redis_queries_db_directly(self):
        from app.utils.location_utils import get_unique_user_locations

        session = make_mock_session()
        db_rows = [_make_location_row("Portland", "OR")]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = db_rows
        session.execute = AsyncMock(return_value=mock_result)

        with patch('app.utils.location_utils.AsyncSessionLocal', return_value=session):
            result = await get_unique_user_locations(redis=None)

        assert result == [("Portland", "OR")]

    async def test_location_values_are_stripped(self):
        """city.strip() / state.strip() should remove leading/trailing whitespace."""
        from app.utils.location_utils import get_unique_user_locations

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        session = make_mock_session()
        row = _make_location_row("  Austin  ", "  TX  ")
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [row]
        session.execute = AsyncMock(return_value=mock_result)

        with patch('app.utils.location_utils.AsyncSessionLocal', return_value=session):
            result = await get_unique_user_locations(redis=mock_redis)

        assert result == [("Austin", "TX")]
