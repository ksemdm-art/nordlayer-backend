"""
Cache management endpoints for administrators.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_admin_user
from app.services.cache_service import cache_service
from app.services.model_optimization import model_optimization_service
from app.models.user import User

router = APIRouter()


@router.get("/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_admin_user)
):
    """Get cache statistics (Admin only)"""
    try:
        stats = await cache_service.get_stats()
        return {
            "success": True,
            "data": stats,
            "message": "Cache statistics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")


@router.delete("/clear")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="Pattern to match keys (e.g., 'projects:*')"),
    current_user: User = Depends(get_current_admin_user)
):
    """Clear cache data (Admin only)"""
    try:
        if pattern:
            deleted_count = await cache_service.delete_pattern(pattern)
            message = f"Deleted {deleted_count} cache keys matching pattern '{pattern}'"
        else:
            success = await cache_service.flush_all()
            if success:
                message = "All cache data cleared successfully"
            else:
                raise HTTPException(status_code=500, detail="Failed to clear cache")
        
        return {
            "success": True,
            "data": {"deleted_keys": deleted_count if pattern else "all"},
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@router.post("/warm-up")
async def warm_up_cache(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Warm up cache with frequently accessed data (Admin only)"""
    try:
        # Add background task to warm up cache
        background_tasks.add_task(_warm_up_cache_task, db)
        
        return {
            "success": True,
            "data": None,
            "message": "Cache warm-up started in background"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting cache warm-up: {str(e)}")


@router.get("/keys")
async def list_cache_keys(
    pattern: str = Query("*", description="Pattern to match keys"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of keys to return"),
    current_user: User = Depends(get_current_admin_user)
):
    """List cache keys matching pattern (Admin only)"""
    try:
        if not cache_service.enabled:
            return {
                "success": False,
                "data": [],
                "message": "Cache is not enabled"
            }
        
        # Get keys matching pattern (limited implementation)
        # Note: This is a simplified version - in production you might want to use SCAN
        keys = []
        if cache_service.redis_client:
            all_keys = await cache_service.redis_client.keys(pattern)
            keys = all_keys[:limit]
        
        return {
            "success": True,
            "data": {
                "keys": keys,
                "total_shown": len(keys),
                "pattern": pattern
            },
            "message": f"Found {len(keys)} cache keys"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing cache keys: {str(e)}")


@router.delete("/key/{key}")
async def delete_cache_key(
    key: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Delete specific cache key (Admin only)"""
    try:
        success = await cache_service.delete(key)
        
        if success:
            return {
                "success": True,
                "data": {"key": key},
                "message": f"Cache key '{key}' deleted successfully"
            }
        else:
            return {
                "success": False,
                "data": {"key": key},
                "message": f"Cache key '{key}' not found or could not be deleted"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting cache key: {str(e)}")


@router.get("/key/{key}")
async def get_cache_key(
    key: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Get value of specific cache key (Admin only)"""
    try:
        value = await cache_service.get(key)
        
        if value is not None:
            return {
                "success": True,
                "data": {
                    "key": key,
                    "value": value,
                    "exists": True
                },
                "message": f"Cache key '{key}' retrieved successfully"
            }
        else:
            return {
                "success": False,
                "data": {
                    "key": key,
                    "value": None,
                    "exists": False
                },
                "message": f"Cache key '{key}' not found"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache key: {str(e)}")


@router.post("/optimize-models")
async def optimize_models(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user)
):
    """Start model optimization process (Admin only)"""
    try:
        # Add background task to optimize models
        background_tasks.add_task(_optimize_models_task)
        
        return {
            "success": True,
            "data": None,
            "message": "Model optimization started in background"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting model optimization: {str(e)}")


@router.post("/cleanup-optimized")
async def cleanup_optimized_models(
    background_tasks: BackgroundTasks,
    max_age_days: int = Query(7, ge=1, le=30, description="Maximum age in days"),
    current_user: User = Depends(get_current_admin_user)
):
    """Clean up old optimized model files (Admin only)"""
    try:
        # Add background task to clean up optimized files
        background_tasks.add_task(_cleanup_optimized_task, max_age_days)
        
        return {
            "success": True,
            "data": {"max_age_days": max_age_days},
            "message": f"Cleanup of optimized files older than {max_age_days} days started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting cleanup: {str(e)}")


# Background tasks
async def _warm_up_cache_task(db: Session):
    """Background task to warm up cache"""
    try:
        from app.services.project import project_service
        from app.crud import article as crud_article, service as crud_service
        
        # Warm up projects cache
        projects = project_service.get_projects_with_filters(db, skip=0, limit=20)
        for project in projects:
            cache_key = f"project:{project.id}"
            project_dict = project.__dict__ if hasattr(project, '__dict__') else project
            await cache_service.set(cache_key, project_dict, 3600)
        
        # Warm up articles cache
        articles = crud_article.get_published(db, skip=0, limit=20)
        for article in articles:
            cache_key = f"article:{article.id}"
            article_dict = {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "excerpt": article.excerpt,
                "featured_image": article.featured_image,
                "category": article.category,
                "status": article.status or "draft",
                "views": article.views or 0,
                "created_at": article.created_at.isoformat() if article.created_at else None,
                "updated_at": article.updated_at.isoformat() if article.updated_at else None,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "is_published": article.is_published,
                "slug": article.slug,
                "tags": article.tags
            }
            await cache_service.set(cache_key, article_dict, 1800)
        
        # Warm up services cache
        services = crud_service.get_active(db, skip=0, limit=50)
        for service in services:
            cache_key = f"service:{service.id}"
            service_dict = service.__dict__ if hasattr(service, '__dict__') else service
            await cache_service.set(cache_key, service_dict, 7200)
        
        print(f"Cache warmed up: {len(projects)} projects, {len(articles)} articles, {len(services)} services")
        
    except Exception as e:
        print(f"Error warming up cache: {e}")


async def _optimize_models_task():
    """Background task to optimize 3D models"""
    try:
        from pathlib import Path
        from app.core.config import settings
        
        upload_dir = Path(settings.upload_dir)
        model_files = []
        
        # Find all model files
        for ext in ['.stl', '.obj', '.3mf']:
            model_files.extend(upload_dir.rglob(f'*{ext}'))
        
        optimized_count = 0
        for model_file in model_files:
            try:
                optimized_url = await model_optimization_service.get_optimized_model_url(str(model_file))
                if optimized_url:
                    optimized_count += 1
            except Exception as e:
                print(f"Error optimizing {model_file}: {e}")
        
        print(f"Model optimization completed: {optimized_count}/{len(model_files)} files optimized")
        
    except Exception as e:
        print(f"Error in model optimization task: {e}")


async def _cleanup_optimized_task(max_age_days: int):
    """Background task to clean up optimized files"""
    try:
        stats = await model_optimization_service.cleanup_old_optimized_files(max_age_days)
        print(f"Optimized files cleanup completed: {stats}")
    except Exception as e:
        print(f"Error in cleanup task: {e}")