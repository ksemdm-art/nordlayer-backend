"""
Redis cache service for caching frequently accessed data.
"""
import json
import logging
from typing import Any, Optional, Dict, List
from datetime import timedelta
import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for Redis caching operations"""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.enabled = False
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.enabled = True
            logger.info("Redis cache service initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis: {e}. Caching disabled.")
            self.enabled = False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or cache disabled
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            if expire:
                await self.redis_client.setex(key, expire, serialized_value)
            else:
                await self.redis_client.set(key, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Pattern to match (e.g., "projects:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Error deleting cache pattern {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache key existence {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment numeric value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value or None if error
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            return await self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing cache key {key}: {e}")
            return None
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for key.
        
        Args:
            key: Cache key
            seconds: Expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            return bool(await self.redis_client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Error setting expiration for cache key {key}: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled or not self.redis_client:
            return {"enabled": False, "error": "Redis not available"}
        
        try:
            info = await self.redis_client.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": False, "error": str(e)}
    
    async def flush_all(self) -> bool:
        """
        Clear all cache data.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            await self.redis_client.flushall()
            logger.info("Cache flushed successfully")
            return True
        except Exception as e:
            logger.error(f"Error flushing cache: {e}")
            return False
    
    async def connect(self):
        """Connect to Redis (for compatibility with middleware)"""
        if not self.enabled:
            self._initialize_redis()
        logger.info("Cache service connection established")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        await self.close()
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")


class CacheKeys:
    """Cache key constants and generators"""
    
    # Projects
    PROJECTS_LIST = "projects:list:{skip}:{limit}:{category}"
    PROJECT_DETAIL = "project:{project_id}"
    PROJECTS_CATEGORIES = "projects:categories"
    
    # Articles
    ARTICLES_LIST = "articles:list:{skip}:{limit}:{category}"
    ARTICLE_DETAIL = "article:{article_id}"
    ARTICLES_CATEGORIES = "articles:categories"
    
    # Services
    SERVICES_LIST = "services:list:{active_only}"
    SERVICE_DETAIL = "service:{service_id}"
    
    # Orders
    ORDER_STATS = "orders:stats:{date_range}"
    
    # File stats
    FILE_STATS = "files:stats"
    
    @staticmethod
    def projects_list(skip: int = 0, limit: int = 100, category: Optional[str] = None) -> str:
        """Generate cache key for projects list"""
        return CacheKeys.PROJECTS_LIST.format(
            skip=skip, 
            limit=limit, 
            category=category or "all"
        )
    
    @staticmethod
    def project_detail(project_id: int) -> str:
        """Generate cache key for project detail"""
        return CacheKeys.PROJECT_DETAIL.format(project_id=project_id)
    
    @staticmethod
    def articles_list(skip: int = 0, limit: int = 100, category: Optional[str] = None) -> str:
        """Generate cache key for articles list"""
        return CacheKeys.ARTICLES_LIST.format(
            skip=skip, 
            limit=limit, 
            category=category or "all"
        )
    
    @staticmethod
    def article_detail(article_id: int) -> str:
        """Generate cache key for article detail"""
        return CacheKeys.ARTICLE_DETAIL.format(article_id=article_id)
    
    @staticmethod
    def services_list(active_only: bool = True) -> str:
        """Generate cache key for services list"""
        return CacheKeys.SERVICES_LIST.format(active_only=active_only)
    
    @staticmethod
    def service_detail(service_id: int) -> str:
        """Generate cache key for service detail"""
        return CacheKeys.SERVICE_DETAIL.format(service_id=service_id)


# Cache decorators
def cache_result(key_func, expire: int = 3600):
    """
    Decorator to cache function results.
    
    Args:
        key_func: Function to generate cache key
        expire: Expiration time in seconds
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = key_func(*args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, expire)
            logger.debug(f"Cache set for key: {cache_key}")
            
            return result
        return wrapper
    return decorator


# Global cache service instance
cache_service = CacheService()