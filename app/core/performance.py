"""
Performance optimization utilities and configurations
"""
import asyncio
import time
from functools import wraps
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import redis
import json
import hashlib
from app.core.config import settings


class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.metrics = {}
        
    def track_endpoint(self, endpoint: str, duration: float, status_code: int):
        """Track endpoint performance"""
        if endpoint not in self.metrics:
            self.metrics[endpoint] = {
                'total_requests': 0,
                'total_duration': 0,
                'avg_duration': 0,
                'max_duration': 0,
                'min_duration': float('inf'),
                'error_count': 0
            }
        
        metric = self.metrics[endpoint]
        metric['total_requests'] += 1
        metric['total_duration'] += duration
        metric['avg_duration'] = metric['total_duration'] / metric['total_requests']
        metric['max_duration'] = max(metric['max_duration'], duration)
        metric['min_duration'] = min(metric['min_duration'], duration)
        
        if status_code >= 400:
            metric['error_count'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {}


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def performance_tracker(func):
    """Decorator to track function performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            performance_monitor.track_endpoint(
                func.__name__, 
                duration, 
                200
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            performance_monitor.track_endpoint(
                func.__name__, 
                duration, 
                500
            )
            raise
    return wrapper


class CacheManager:
    """Redis-based caching for performance optimization"""
    
    def __init__(self):
        self.redis_client = None
        if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL)
            except Exception:
                self.redis_client = None
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters"""
        # Filter out non-serializable objects like SQLAlchemy Session
        serializable_kwargs = {}
        for key, value in kwargs.items():
            try:
                # Skip database sessions and other non-serializable objects
                if hasattr(value, '__class__') and 'Session' in str(type(value)):
                    continue
                json.dumps(value)  # Test if serializable
                serializable_kwargs[key] = value
            except (TypeError, ValueError):
                # Skip non-serializable values
                continue
        
        key_data = json.dumps(serializable_kwargs, sort_keys=True)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception:
            pass
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(
                key, 
                ttl, 
                json.dumps(value, default=str)
            )
        except Exception:
            pass
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.delete(key)
        except Exception:
            pass
    
    def cache_response(self, prefix: str, ttl: int = 300):
        """Decorator for caching endpoint responses"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from function arguments
                cache_key = self._generate_cache_key(prefix, **kwargs)
                
                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator


# Global cache manager instance
cache_manager = CacheManager()


class DatabaseOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def optimize_query_params(
        page: int = 1, 
        limit: int = 20, 
        max_limit: int = 100
    ) -> tuple:
        """Optimize pagination parameters"""
        page = max(1, page)
        limit = min(max(1, limit), max_limit)
        offset = (page - 1) * limit
        return offset, limit
    
    @staticmethod
    def build_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build optimized database filters"""
        optimized_filters = {}
        
        for key, value in filters.items():
            if value is not None and value != "":
                # Handle different filter types
                if key.endswith('_like'):
                    # Text search optimization
                    field_name = key.replace('_like', '')
                    optimized_filters[field_name] = f"%{value}%"
                elif key.endswith('_in'):
                    # List filters
                    field_name = key.replace('_in', '')
                    if isinstance(value, str):
                        optimized_filters[field_name] = value.split(',')
                    else:
                        optimized_filters[field_name] = value
                else:
                    optimized_filters[key] = value
        
        return optimized_filters


class ResponseOptimizer:
    """Response optimization utilities"""
    
    @staticmethod
    def compress_response(data: Any, threshold: int = 1024) -> Any:
        """Compress large responses"""
        # For now, just return data as-is
        # In production, implement gzip compression
        return data
    
    @staticmethod
    def paginate_response(
        data: list, 
        total: int, 
        page: int, 
        limit: int
    ) -> Dict[str, Any]:
        """Create optimized paginated response"""
        total_pages = (total + limit - 1) // limit
        
        return {
            "data": data,
            "pagination": {
                "page": page,
                "per_page": limit,  # Changed from 'limit' to 'per_page'
                "total": total,
                "pages": total_pages,  # Changed from 'total_pages' to 'pages'
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }


# Performance middleware
async def performance_middleware(request: Request, call_next):
    """Middleware to track request performance"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    endpoint = f"{request.method} {request.url.path}"
    
    performance_monitor.track_endpoint(
        endpoint, 
        duration, 
        response.status_code
    )
    
    # Add performance headers
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    
    return response


# Health check endpoint for performance monitoring
async def get_performance_metrics():
    """Get current performance metrics"""
    return {
        "status": "healthy",
        "metrics": performance_monitor.get_metrics(),
        "cache_status": "enabled" if cache_manager.redis_client else "disabled"
    }