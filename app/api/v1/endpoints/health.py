"""
Health check and monitoring endpoints.
"""
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.alerting import alert_manager
from app.core.monitoring_middleware import metrics_endpoint
from app.schemas.response import HealthResponse, AlertResponse

logger = get_logger("health")
router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint.
    Returns system status and component health.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "components": {}
    }
    
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {
            "status": "healthy",
            "response_time_ms": 0  # Could measure actual response time
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check file system
    try:
        import os
        import tempfile
        
        # Test write/read/delete
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(b"health check")
            tmp.flush()
            
        health_status["components"]["filesystem"] = {
            "status": "healthy"
        }
    except Exception as e:
        logger.error(f"Filesystem health check failed: {e}")
        health_status["components"]["filesystem"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check system resources
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status["components"]["system"] = {
            "status": "healthy",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": (disk.used / disk.total) * 100
        }
        
        # Mark as degraded if resources are high
        if cpu_percent > 90 or memory.percent > 90:
            health_status["components"]["system"]["status"] = "degraded"
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
                
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        health_status["components"]["system"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Return appropriate HTTP status
    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return health_status

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check for Kubernetes/Docker.
    Returns 200 if service is ready to accept traffic.
    """
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not ready", "error": str(e)}
        )

@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/Docker.
    Returns 200 if service is alive.
    """
    return {
        "status": "alive", 
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@router.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint.
    """
    return await metrics_endpoint()

@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts():
    """
    Get active alerts.
    """
    alerts = alert_manager.get_active_alerts()
    return [
        {
            "id": alert.id,
            "type": alert.type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat() + "Z",
            "metadata": alert.metadata
        }
        for alert in alerts
    ]

@router.get("/alerts/history", response_model=List[AlertResponse])
async def get_alert_history(limit: int = 50):
    """
    Get alert history.
    """
    alerts = alert_manager.get_alert_history(limit)
    return [
        {
            "id": alert.id,
            "type": alert.type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat() + "Z",
            "resolved": alert.resolved,
            "resolved_at": alert.resolved_at.isoformat() + "Z" if alert.resolved_at else None,
            "metadata": alert.metadata
        }
        for alert in alerts
    ]

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """
    Resolve an active alert.
    """
    alert_manager.resolve_alert(alert_id)
    return {"message": f"Alert {alert_id} resolved"}

@router.get("/status")
async def get_system_status():
    """
    Get comprehensive system status including metrics and alerts.
    """
    import psutil
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Active alerts
    active_alerts = alert_manager.get_active_alerts()
    
    # Recent alert history
    recent_alerts = alert_manager.get_alert_history(10)
    
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
            "disk_percent": (disk.used / disk.total) * 100,
            "disk_used_gb": disk.used / (1024**3),
            "disk_total_gb": disk.total / (1024**3)
        },
        "alerts": {
            "active_count": len(active_alerts),
            "critical_count": len([a for a in active_alerts if a.severity.value == "critical"]),
            "high_count": len([a for a in active_alerts if a.severity.value == "high"]),
            "recent": [
                {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "timestamp": alert.timestamp.isoformat() + "Z"
                }
                for alert in recent_alerts
            ]
        },
        "uptime": {
            # Could track actual uptime
            "status": "running"
        }
    }

@router.get("/dashboard")
async def monitoring_dashboard():
    """
    Serve the monitoring dashboard HTML page.
    """
    from fastapi.responses import FileResponse
    import os
    
    dashboard_path = os.path.join(
        os.path.dirname(__file__), 
        "..", "..", "..", "static", "monitoring", "dashboard.html"
    )
    
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path, media_type="text/html")
    else:
        raise HTTPException(
            status_code=404,
            detail="Monitoring dashboard not found"
        )