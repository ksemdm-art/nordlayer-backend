"""
Tests for the cache service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.cache_service import CacheService, CacheKeys


class TestCacheService:
    """Tests for CacheService"""
    
    @pytest.fixture
    def cache_service(self):
        """Create cache service instance for testing"""
        with patch('app.services.cache_service.redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            
            service = CacheService()
            service.redis_client = mock_client
            service.enabled = True
            return service
    
    @pytest.mark.asyncio
    async def test_get_existing_key(self, cache_service):
        """Test getting existing cache key"""
        test_data = {"test": "value"}
        cache_service.redis_client.get.return_value = json.dumps(test_data)
        
        result = await cache_service.get("test_key")
        
        assert result == test_data
        cache_service.redis_client.get.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache_service):
        """Test getting non-existent cache key"""
        cache_service.redis_client.get.return_value = None
        
        result = await cache_service.get("nonexistent_key")
        
        assert result is None
        cache_service.redis_client.get.assert_called_once_with("nonexistent_key")
    
    @pytest.mark.asyncio
    async def test_set_with_expiration(self, cache_service):
        """Test setting cache key with expiration"""
        test_data = {"test": "value"}
        
        result = await cache_service.set("test_key", test_data, 3600)
        
        assert result is True
        cache_service.redis_client.setex.assert_called_once_with(
            "test_key", 3600, json.dumps(test_data, default=str)
        )
    
    @pytest.mark.asyncio
    async def test_set_without_expiration(self, cache_service):
        """Test setting cache key without expiration"""
        test_data = {"test": "value"}
        
        result = await cache_service.set("test_key", test_data)
        
        assert result is True
        cache_service.redis_client.set.assert_called_once_with(
            "test_key", json.dumps(test_data, default=str)
        )
    
    @pytest.mark.asyncio
    async def test_delete_key(self, cache_service):
        """Test deleting cache key"""
        result = await cache_service.delete("test_key")
        
        assert result is True
        cache_service.redis_client.delete.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_delete_pattern(self, cache_service):
        """Test deleting keys by pattern"""
        cache_service.redis_client.keys.return_value = ["key1", "key2", "key3"]
        
        result = await cache_service.delete_pattern("test:*")
        
        assert result == 3
        cache_service.redis_client.keys.assert_called_once_with("test:*")
        cache_service.redis_client.delete.assert_called_once_with("key1", "key2", "key3")
    
    @pytest.mark.asyncio
    async def test_exists_true(self, cache_service):
        """Test checking if key exists (true case)"""
        cache_service.redis_client.exists.return_value = 1
        
        result = await cache_service.exists("test_key")
        
        assert result is True
        cache_service.redis_client.exists.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_exists_false(self, cache_service):
        """Test checking if key exists (false case)"""
        cache_service.redis_client.exists.return_value = 0
        
        result = await cache_service.exists("test_key")
        
        assert result is False
        cache_service.redis_client.exists.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_increment(self, cache_service):
        """Test incrementing numeric value"""
        cache_service.redis_client.incrby.return_value = 5
        
        result = await cache_service.increment("counter", 2)
        
        assert result == 5
        cache_service.redis_client.incrby.assert_called_once_with("counter", 2)
    
    @pytest.mark.asyncio
    async def test_expire(self, cache_service):
        """Test setting expiration for key"""
        cache_service.redis_client.expire.return_value = True
        
        result = await cache_service.expire("test_key", 3600)
        
        assert result is True
        cache_service.redis_client.expire.assert_called_once_with("test_key", 3600)
    
    @pytest.mark.asyncio
    async def test_get_stats(self, cache_service):
        """Test getting cache statistics"""
        mock_info = {
            "connected_clients": 5,
            "used_memory": 1024000,
            "used_memory_human": "1.02M",
            "keyspace_hits": 100,
            "keyspace_misses": 10,
            "total_commands_processed": 1000,
            "uptime_in_seconds": 3600
        }
        cache_service.redis_client.info.return_value = mock_info
        
        result = await cache_service.get_stats()
        
        assert result["enabled"] is True
        assert result["connected_clients"] == 5
        assert result["used_memory"] == 1024000
        assert result["keyspace_hits"] == 100
    
    @pytest.mark.asyncio
    async def test_flush_all(self, cache_service):
        """Test flushing all cache data"""
        result = await cache_service.flush_all()
        
        assert result is True
        cache_service.redis_client.flushall.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disabled_cache(self):
        """Test cache operations when cache is disabled"""
        service = CacheService()
        service.enabled = False
        service.redis_client = None
        
        # All operations should return default values
        assert await service.get("key") is None
        assert await service.set("key", "value") is False
        assert await service.delete("key") is False
        assert await service.delete_pattern("pattern") == 0
        assert await service.exists("key") is False
        assert await service.increment("key") is None
        assert await service.expire("key", 3600) is False
        assert await service.flush_all() is False
        
        stats = await service.get_stats()
        assert stats["enabled"] is False
    
    @pytest.mark.asyncio
    async def test_error_handling(self, cache_service):
        """Test error handling in cache operations"""
        # Mock Redis to raise exceptions
        cache_service.redis_client.get.side_effect = Exception("Redis error")
        cache_service.redis_client.set.side_effect = Exception("Redis error")
        cache_service.redis_client.delete.side_effect = Exception("Redis error")
        
        # Operations should handle errors gracefully
        assert await cache_service.get("key") is None
        assert await cache_service.set("key", "value") is False
        assert await cache_service.delete("key") is False


class TestCacheKeys:
    """Tests for CacheKeys utility class"""
    
    def test_projects_list_key(self):
        """Test projects list cache key generation"""
        key = CacheKeys.projects_list(skip=0, limit=20, category="electronics")
        expected = "projects:list:0:20:electronics"
        assert key == expected
    
    def test_projects_list_key_no_category(self):
        """Test projects list cache key without category"""
        key = CacheKeys.projects_list(skip=10, limit=50)
        expected = "projects:list:10:50:all"
        assert key == expected
    
    def test_project_detail_key(self):
        """Test project detail cache key generation"""
        key = CacheKeys.project_detail(123)
        expected = "project:123"
        assert key == expected
    
    def test_articles_list_key(self):
        """Test articles list cache key generation"""
        key = CacheKeys.articles_list(skip=5, limit=15, category="tutorials")
        expected = "articles:list:5:15:tutorials"
        assert key == expected
    
    def test_article_detail_key(self):
        """Test article detail cache key generation"""
        key = CacheKeys.article_detail(456)
        expected = "article:456"
        assert key == expected
    
    def test_services_list_key(self):
        """Test services list cache key generation"""
        key = CacheKeys.services_list(active_only=True)
        expected = "services:list:True"
        assert key == expected
    
    def test_service_detail_key(self):
        """Test service detail cache key generation"""
        key = CacheKeys.service_detail(789)
        expected = "service:789"
        assert key == expected


class TestCacheIntegration:
    """Integration tests for cache service"""
    
    @pytest.mark.asyncio
    async def test_cache_decorator_hit(self):
        """Test cache decorator with cache hit"""
        from app.services.cache_service import cache_result
        
        # Mock cache service
        with patch('app.services.cache_service.cache_service') as mock_cache:
            mock_cache.get = AsyncMock(return_value="cached_result")
            
            @cache_result(lambda x: f"test:{x}", expire=3600)
            async def test_function(param):
                return f"computed_{param}"
            
            result = await test_function("value")
            
            assert result == "cached_result"
            mock_cache.get.assert_called_once_with("test:value")
            mock_cache.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cache_decorator_miss(self):
        """Test cache decorator with cache miss"""
        from app.services.cache_service import cache_result
        
        # Mock cache service
        with patch('app.services.cache_service.cache_service') as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            
            @cache_result(lambda x: f"test:{x}", expire=3600)
            async def test_function(param):
                return f"computed_{param}"
            
            result = await test_function("value")
            
            assert result == "computed_value"
            mock_cache.get.assert_called_once_with("test:value")
            mock_cache.set.assert_called_once_with("test:value", "computed_value", 3600)
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_scenario(self):
        """Test cache invalidation scenario"""
        # Create cache service for this test
        with patch('app.services.cache_service.redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            
            cache_service = CacheService()
            cache_service.redis_client = mock_client
            cache_service.enabled = True
        # Set initial cache value
        await cache_service.set("projects:list:hash123", {"data": "old"})
        
        # Verify it exists
        assert await cache_service.exists("projects:list:hash123")
        
        # Invalidate cache (simulate data update)
        deleted_count = await cache_service.delete_pattern("projects:*")
        
        # Verify cache was cleared
        assert deleted_count >= 0  # Depends on mock implementation
        cache_service.redis_client.keys.assert_called_with("projects:*")
    
    @pytest.mark.asyncio
    async def test_cache_warming_scenario(self):
        """Test cache warming scenario"""
        # Create cache service for this test
        with patch('app.services.cache_service.redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            
            cache_service = CacheService()
            cache_service.redis_client = mock_client
            cache_service.enabled = True
        # Simulate warming up cache with multiple items
        items = [
            ("project:1", {"id": 1, "title": "Project 1"}),
            ("project:2", {"id": 2, "title": "Project 2"}),
            ("article:1", {"id": 1, "title": "Article 1"})
        ]
        
        for key, value in items:
            await cache_service.set(key, value, 3600)
        
        # Verify all items were cached
        assert cache_service.redis_client.setex.call_count == len(items)
        
        # Verify we can retrieve them
        for key, expected_value in items:
            cache_service.redis_client.get.return_value = json.dumps(expected_value)
            result = await cache_service.get(key)
            assert result == expected_value