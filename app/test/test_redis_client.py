"""
Tests for app/utils/redis_client.py

Covers: init_redis, close_redis, get_redis_client
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import app.utils.redis_client as redis_module


class TestInitRedis:

    def teardown_method(self):
        redis_module._redis_client = None

    @pytest.mark.asyncio
    async def test_no_redis_url_sets_client_to_none(self):
        env = {k: v for k, v in os.environ.items() if k != "REDIS_URL"}
        with patch.dict(os.environ, env, clear=True):
            await redis_module.init_redis()
        assert redis_module._redis_client is None

    @pytest.mark.asyncio
    async def test_successful_connection_sets_client(self):
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        with patch.dict(os.environ, {"REDIS_URL": "rediss://localhost:6379"}):
            with patch("redis.asyncio.from_url", return_value=mock_client):
                await redis_module.init_redis()
        assert redis_module._redis_client is mock_client
        mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_failure_sets_client_to_none(self):
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("Connection refused"))
        with patch.dict(os.environ, {"REDIS_URL": "rediss://localhost:6379"}):
            with patch("redis.asyncio.from_url", return_value=mock_client):
                await redis_module.init_redis()
        assert redis_module._redis_client is None

    @pytest.mark.asyncio
    async def test_does_not_raise_on_failure(self):
        with patch.dict(os.environ, {"REDIS_URL": "rediss://bad-host:6379"}):
            with patch("redis.asyncio.from_url", side_effect=Exception("DNS error")):
                await redis_module.init_redis()  # Must not raise
        assert redis_module._redis_client is None


class TestGetRedisClient:

    def teardown_method(self):
        redis_module._redis_client = None

    def test_returns_none_when_not_initialized(self):
        redis_module._redis_client = None
        assert redis_module.get_redis_client() is None

    def test_returns_client_after_init(self):
        mock_client = MagicMock()
        redis_module._redis_client = mock_client
        assert redis_module.get_redis_client() is mock_client

    def test_returns_same_singleton(self):
        mock_client = MagicMock()
        redis_module._redis_client = mock_client
        assert redis_module.get_redis_client() is redis_module.get_redis_client()


class TestCloseRedis:

    def teardown_method(self):
        redis_module._redis_client = None

    @pytest.mark.asyncio
    async def test_aclose_called_and_client_set_to_none(self):
        mock_client = AsyncMock()
        redis_module._redis_client = mock_client
        await redis_module.close_redis()
        mock_client.aclose.assert_called_once()
        assert redis_module._redis_client is None

    @pytest.mark.asyncio
    async def test_close_when_none_does_not_raise(self):
        redis_module._redis_client = None
        await redis_module.close_redis()  # Must not raise

    @pytest.mark.asyncio
    async def test_close_is_idempotent(self):
        mock_client = AsyncMock()
        redis_module._redis_client = mock_client
        await redis_module.close_redis()
        await redis_module.close_redis()  # Second call must not raise
