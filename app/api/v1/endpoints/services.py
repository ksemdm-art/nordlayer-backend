from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import service
from app.schemas.service import Service, ServiceCreate, ServiceUpdate, ServiceSummary
from app.schemas.response import DataResponse, ListResponse
from app.services.cache_service import cache_service, CacheKeys

router = APIRouter()

async def invalidate_services_cache():
    """Invalidate all services-related cache entries."""
    try:
        import hashlib
        
        # Генерируем все возможные комбинации параметров для инвалидации
        skip_values = [0]
        limit_values = [3, 20, 100]  # Добавляем limit=3 для главной страницы
        category_values = [None, "3d_printing", "post_processing", "modeling", "consultation"]
        active_only_values = [True, False]
        
        cache_keys_to_delete = []
        
        for skip in skip_values:
            for limit in limit_values:
                for category in category_values:
                    for active_only in active_only_values:
                        cache_key_str = f"{skip}:{limit}:{category}:{active_only}"
                        cache_key_hash = hashlib.md5(cache_key_str.encode()).hexdigest()
                        cache_key = f"services:list:{cache_key_hash}"
                        cache_keys_to_delete.append(cache_key)
        
        # Удаляем все ключи
        for key in cache_keys_to_delete:
            await cache_service.delete(key)
        
        print(f"✅ Services cache invalidated ({len(cache_keys_to_delete)} keys)")
    except Exception as e:
        print(f"⚠️ Cache invalidation error: {e}")

@router.get("/", response_model=ListResponse[ServiceSummary])
async def get_services(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Show only active services")
):
    """Get list of services with optional filtering."""
    try:
        # Create cache key
        import hashlib
        cache_key_str = f"{skip}:{limit}:{category}:{active_only}"
        cache_key_hash = hashlib.md5(cache_key_str.encode()).hexdigest()
        cache_key = f"services:list:{cache_key_hash}"
        
        # Try to get from cache first
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return ListResponse(**cached_result)
        
        if category:
            services = service.get_by_category(db, category=category, skip=skip, limit=limit)
        elif active_only:
            services = service.get_active(db, skip=skip, limit=limit)
        else:
            services = service.get_multi(db, skip=skip, limit=limit)
        
        result = ListResponse(
            success=True,
            data=services,
            message=f"Retrieved {len(services)} services"
        )
        
        # Cache the result for 1 hour
        result_dict = {
            "success": True,
            "data": [s.__dict__ if hasattr(s, '__dict__') else s for s in services],
            "message": f"Retrieved {len(services)} services"
        }
        await cache_service.set(cache_key, result_dict, 3600)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{service_id}", response_model=DataResponse[ServiceSummary])
async def get_service(service_id: int, db: Session = Depends(get_db)):
    """Get service by ID."""
    # Try to get from cache first
    cache_key = CacheKeys.service_detail(service_id)
    cached_service = await cache_service.get(cache_key)
    if cached_service:
        return DataResponse(
            success=True,
            data=cached_service,
            message="Service retrieved successfully"
        )
    
    db_service = service.get(db, id=service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Cache the service for 2 hours
    service_dict = db_service.__dict__ if hasattr(db_service, '__dict__') else db_service
    await cache_service.set(cache_key, service_dict, 7200)
    
    return DataResponse(
        success=True,
        data=db_service,
        message="Service retrieved successfully"
    )

@router.post("/", response_model=DataResponse[ServiceSummary])
async def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db)
):
    """Create a new service."""
    try:
        db_service = service.create(db, obj_in=service_data)
        
        # Инвалидируем кеш после создания
        await invalidate_services_cache()
        
        return DataResponse(
            success=True,
            data=db_service,
            message="Service created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{service_id}", response_model=DataResponse[ServiceSummary])
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db)
):
    """Update a service."""
    print(f"🔄 Updating service {service_id} with data: {service_data.model_dump(exclude_unset=True)}")
    
    db_service = service.get(db, id=service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    print(f"📊 Current service status: {db_service.is_active}")
    
    try:
        updated_service = service.update(db, db_obj=db_service, obj_in=service_data)
        print(f"✅ Updated service status: {updated_service.is_active}")
        
        # Дополнительная проверка - получаем услугу заново из БД
        verification_service = service.get(db, id=service_id)
        print(f"🔍 Verification query - service status: {verification_service.is_active}")
        
        if verification_service.is_active != updated_service.is_active:
            print("❌ WARNING: Status mismatch after update!")
            # Принудительно коммитим еще раз
            db.commit()
            db.refresh(verification_service)
            print(f"🔄 After forced commit: {verification_service.is_active}")
        
        # Инвалидируем кеш после обновления
        await invalidate_services_cache()
        
        # Также удаляем кеш для конкретной услуги
        detail_cache_key = CacheKeys.service_detail(service_id)
        await cache_service.delete(detail_cache_key)
        
        return DataResponse(
            success=True,
            data=verification_service,  # Возвращаем проверенные данные
            message="Service updated successfully"
        )
    except Exception as e:
        print(f"❌ Error updating service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{service_id}")
async def delete_service(service_id: int, db: Session = Depends(get_db)):
    """Permanently delete a service."""
    db_service = service.get(db, id=service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    try:
        success = service.hard_delete(db, id=service_id)
        if success:
            # Инвалидируем кеш после удаления
            await invalidate_services_cache()
            
            return {"success": True, "message": "Service deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete service")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{service_id}/deactivate", response_model=DataResponse[ServiceSummary])
async def deactivate_service(service_id: int, db: Session = Depends(get_db)):
    """Deactivate a service (soft delete)."""
    db_service = service.get(db, id=service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    try:
        deactivated_service = service.deactivate(db, id=service_id)
        
        # Инвалидируем кеш после деактивации
        await invalidate_services_cache()
        
        return DataResponse(
            success=True,
            data=deactivated_service,
            message="Service deactivated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{service_id}/activate", response_model=DataResponse[ServiceSummary])
async def activate_service(service_id: int, db: Session = Depends(get_db)):
    """Activate a service."""
    db_service = service.get(db, id=service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    try:
        activated_service = service.activate(db, id=service_id)
        
        # Инвалидируем кеш после активации
        await invalidate_services_cache()
        
        return DataResponse(
            success=True,
            data=activated_service,
            message="Service activated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/", response_model=ListResponse[ServiceSummary])
async def search_services(
    q: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Search services by name."""
    try:
        services = service.search_by_name(db, name=q, skip=skip, limit=limit)
        return ListResponse(
            success=True,
            data=services,
            message=f"Found {len(services)} services matching '{q}'"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))