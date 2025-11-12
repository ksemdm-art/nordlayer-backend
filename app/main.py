from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from pathlib import Path
from contextlib import asynccontextmanager
import asyncio
import os

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.middleware import (
    LoggingMiddleware,
    ErrorHandlingMiddleware,
    SecurityHeadersMiddleware
)
from app.core.cache_middleware import cache_lifespan, add_cache_headers
from app.core.exceptions import APIError
from app.core.logging_config import setup_logging, get_logger
from app.core.monitoring_middleware import MonitoringMiddleware, system_metrics_collector
from app.core.alerting import setup_alerting, alert_monitoring_loop, alert_manager

# Setup logging
setup_logging(
    log_level=getattr(settings, 'LOG_LEVEL', 'INFO'),
    log_file=getattr(settings, 'LOG_FILE', None)
)

logger = get_logger("main")

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Application lifespan manager with monitoring setup."""
    # Startup
    logger.info("Starting 3D Printing Platform API")
    
    # Start system metrics collection
    await system_metrics_collector.start()
    
    # Setup alerting
    await setup_alerting()
    
    # Start alert monitoring loop
    alert_task = asyncio.create_task(alert_monitoring_loop())
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    # Stop alert monitoring
    alert_task.cancel()
    try:
        await alert_task
    except asyncio.CancelledError:
        pass
    
    # Stop system metrics collection
    await system_metrics_collector.stop()
    
    logger.info("Application shutdown complete")

app = FastAPI(
    title="3D Printing Platform API",
    description="API for 3D printing services platform",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=app_lifespan
)

# Add custom middleware (order matters - first added is outermost)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(MonitoringMiddleware)  # Add monitoring middleware
app.add_middleware(LoggingMiddleware)

# Add cache middleware
app.middleware("http")(add_cache_headers)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    # Record error metrics
    alert_manager.record_metric('http_requests', {
        'status_code': exc.status_code,
        'timestamp': getattr(request.state, 'start_time', None)
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "details": exc.details,
                "type": exc.__class__.__name__
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "Validation error",
                "details": exc.errors(),
                "type": "ValidationError"
            }
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "HTTPException"
            }
        }
    )


# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount uploads directory
uploads_dir = Path(settings.upload_dir)
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)

@app.get("/")
async def root():
    return {"message": "3D Printing Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}