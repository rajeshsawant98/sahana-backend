"""
Tests for app/utils/cache_utils.py

Covers: load_url_cache, save_url_cache — Redis path + file fallback
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, mock_open
from app.utils.cache_utils import load_url_cache, save_url_cache


class TestLoadUrlCache:

    @pytest.mark.asyncio
    async def test_redis_smembers_returns_set(self):
        mock_redis = AsyncMock()
        mock_redis.smembers = AsyncMock(return_value={"https://url1.com", "https://url2.com"})
        result = await load_url_cache(redis=mock_redis)
        assert result == {"https://url1.com", "https://url2.com"}
        mock_redis.smembers.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_failure_falls_back_to_file(self):
        mock_redis = AsyncMock()
        mock_redis.smembers = AsyncMock(side_effect=Exception("Redis unavailable"))
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data='["https://fallback.com"]')):
                result = await load_url_cache(redis=mock_redis)
        assert "https://fallback.com" in result

    @pytest.mark.asyncio
    async def test_no_redis_file_exists_returns_set(self):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data='["https://url1.com", "https://url2.com"]')):
                result = await load_url_cache(redis=None)
        assert result == {"https://url1.com", "https://url2.com"}

    @pytest.mark.asyncio
    async def test_no_redis_no_file_returns_empty_set(self):
        with patch("os.path.exists", return_value=False):
            result = await load_url_cache(redis=None)
        assert result == set()

    @pytest.mark.asyncio
    async def test_no_redis_corrupt_file_returns_empty_set(self):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="not valid json {")):
                result = await load_url_cache(redis=None)
        assert result == set()

    @pytest.mark.asyncio
    async def test_redis_empty_set_returns_empty_set(self):
        mock_redis = AsyncMock()
        mock_redis.smembers = AsyncMock(return_value=set())
        result = await load_url_cache(redis=mock_redis)
        assert result == set()


class TestSaveUrlCache:

    @pytest.mark.asyncio
    async def test_redis_sadd_and_expire_called(self):
        mock_redis = AsyncMock()
        mock_redis.sadd = AsyncMock()
        mock_redis.expire = AsyncMock()
        await save_url_cache({"https://url1.com", "https://url2.com"}, redis=mock_redis)
        mock_redis.sadd.assert_called_once()
        mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_empty_cache_skips_sadd(self):
        mock_redis = AsyncMock()
        mock_redis.sadd = AsyncMock()
        mock_redis.expire = AsyncMock()
        await save_url_cache(set(), redis=mock_redis)
        mock_redis.sadd.assert_not_called()
        mock_redis.expire.assert_not_called()

    @pytest.mark.asyncio
    async def test_redis_failure_falls_back_to_file(self):
        mock_redis = AsyncMock()
        mock_redis.sadd = AsyncMock(side_effect=Exception("Redis error"))
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            await save_url_cache({"https://url1.com"}, redis=mock_redis)
        mock_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_redis_writes_to_file(self):
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            await save_url_cache({"https://url1.com"}, redis=None)
        mock_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_sadd_receives_all_urls(self):
        mock_redis = AsyncMock()
        mock_redis.sadd = AsyncMock()
        mock_redis.expire = AsyncMock()
        urls = {"https://a.com", "https://b.com", "https://c.com"}
        await save_url_cache(urls, redis=mock_redis)
        call_args = mock_redis.sadd.call_args
        # All URLs should be passed as positional args after the key
        passed_urls = set(call_args[0][1:])
        assert passed_urls == urls
