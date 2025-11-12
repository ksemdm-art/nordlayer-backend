"""
Cache middleware for initializing and managing cache connections.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def cache_lifespan(app: FastAPI):
    """Lifespan context manager for cache service"""
    # Startup
    logger.info("Initializing cache service...")
    await cache_service.connect()
    
    yield
    
    # Shutdown
    logger.info("Shutting down cache service...")
    await cache_service.disconnect()


async def add_cache_headers(request, call_next):
    """Add cache-related headers to responses"""
    response = await call_next(request)
    
    # Add cache control headers for static content
    if request.url.path.startswith('/uploads/'):
        if any(request.url.path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
            response.headers["Cache-Control"] = "public, max-age=2592000"  # 30 days
        elif any(request.url.path.endswith(ext) for ext in ['.stl', '.obj', '.3mf']):
            response.headers["Cache-Control"] = "public, max-age=604800"   # 7 days
    
    # Add cache headers for API responses
    elif request.url.path.startswith('/api/'):
        if request.method == "GET":
            # Cache GET requests for a short time
            response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
        else:
            # Don't cache non-GET requests
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    return response