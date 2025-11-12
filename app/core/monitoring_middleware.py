"""
Monitoring middleware for API performance tracking and metrics collection.
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import psutil
import asyncio
from contextlib import asynccontextmanager

from app.core.logging_config import get_logger, log_api_call, log_error

logger = get_logger("monitoring")

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

ERROR_COUNT = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'error_type']
)

# System metrics
CPU_USAGE = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('system_memory_usage_bytes', 'Memory usage in bytes')
DISK_USAGE = Gauge('system_disk_usage_percent', 'Disk usage percentage')

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring API performance and collecting metrics."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ['/health', '/metrics', '/docs', '/redoc']
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        
        # Skip monitoring for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract request info
        method = request.method
        endpoint = self._get_endpoint_pattern(request)
        user_id = getattr(request.state, 'user_id', None)
        
        # Start timing
        start_time = time.time()
        ACTIVE_REQUESTS.inc()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            # Update metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # Log API call
            log_api_call(
                logger, method, endpoint, 
                response.status_code, duration_ms, user_id
            )
            
            # Add monitoring headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            return response
            
        except Exception as e:
            # Calculate duration for error case
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            # Update error metrics
            ERROR_COUNT.labels(
                method=method,
                endpoint=endpoint,
                error_type=type(e).__name__
            ).inc()
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=500
            ).inc()
            
            # Log error
            log_error(logger, e, {
                'request_id': request_id,
                'method': method,
                'endpoint': endpoint,
                'duration': duration_ms,
                'user_id': user_id
            })
            
            raise
        
        finally:
            ACTIVE_REQUESTS.dec()
    
    def _get_endpoint_pattern(self, request: Request) -> str:
        """Extract endpoint pattern from request."""
        # Try to get route pattern
        if hasattr(request, 'scope') and 'route' in request.scope:
            route = request.scope['route']
            if hasattr(route, 'path'):
                return route.path
        
        # Fallback to path with parameter normalization
        path = request.url.path
        
        # Normalize common patterns
        import re
        # Replace UUIDs with {id}
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)
        # Replace numeric IDs with {id}
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path

class SystemMetricsCollector:
    """Collector for system-level metrics."""
    
    def __init__(self, collection_interval: int = 30):
        self.collection_interval = collection_interval
        self.running = False
        self.task = None
    
    async def start(self):
        """Start collecting system metrics."""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._collect_loop())
        logger.info("System metrics collection started")
    
    async def stop(self):
        """Stop collecting system metrics."""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("System metrics collection stopped")
    
    async def _collect_loop(self):
        """Main collection loop."""
        while self.running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_error(logger, e, {'component': 'system_metrics_collector'})
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_metrics(self):
        """Collect system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.used)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            DISK_USAGE.set(disk_percent)
            
            logger.debug(
                "System metrics collected",
                extra={
                    'cpu_percent': cpu_percent,
                    'memory_used_mb': memory.used / 1024 / 1024,
                    'disk_percent': disk_percent
                }
            )
            
        except Exception as e:
            log_error(logger, e, {'component': 'system_metrics_collection'})

# Global system metrics collector instance
system_metrics_collector = SystemMetricsCollector()

@asynccontextmanager
async def monitoring_lifespan(app):
    """Lifespan context manager for monitoring setup."""
    # Startup
    await system_metrics_collector.start()
    logger.info("Monitoring system initialized")
    
    yield
    
    # Shutdown
    await system_metrics_collector.stop()
    logger.info("Monitoring system shutdown")

async def metrics_endpoint():
    """Endpoint to expose Prometheus metrics."""
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )