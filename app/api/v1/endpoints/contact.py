from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.deps import get_db, get_current_admin_user
from app.crud import contact_request as crud_contact_request
from app.models.user import User
from app.schemas.contact_request import (
    ContactRequest, ContactRequestCreate, ContactRequestUpdate, 
    ContactRequestAdminUpdate, ContactRequestSummary, ContactStatus
)

router = APIRouter()


def contact_request_to_dict(contact_request) -> dict:
    """Convert ContactRequest model to dictionary for API response"""
    return {
        "id": contact_request.id,
        "name": contact_request.name,
        "email": contact_request.email,
        "phone": contact_request.phone,
        "subject": contact_request.subject,
        "message": contact_request.message,
        "status": contact_request.status.value if contact_request.status else ContactStatus.NEW.value,
        "admin_notes": contact_request.admin_notes,
        "created_at": contact_request.created_at,
        "updated_at": contact_request.updated_at
    }


# Публичные endpoints

@router.post("/", response_model=dict)
def create_contact_request(
    contact_data: ContactRequestCreate,
    db: Session = Depends(get_db)
):
    """
    Создать новый запрос обратной связи (публичный endpoint)
    """
    try:
        contact_request = crud_contact_request.create(db, obj_in=contact_data)
        return {
            "success": True,
            "data": contact_request_to_dict(contact_request),
            "message": "Ваш запрос успешно отправлен. Мы свяжемся с вами в ближайшее время."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка создания запроса: {str(e)}"
        )


# Административные endpoints

@router.get("/admin/", response_model=dict)
def get_contact_requests_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[ContactStatus] = Query(None, alias="status"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    order_by: str = Query("created_at"),
    order_desc: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить список запросов обратной связи с фильтрацией (только для администраторов)
    """
    contact_requests = crud_contact_request.get_multi_filtered(
        db,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        search_term=search,
        skip=skip,
        limit=limit,
        order_by=order_by,
        order_desc=order_desc
    )
    
    # Получаем общее количество для пагинации
    total_count = crud_contact_request.count_filtered(
        db,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        search_term=search
    )
    
    contact_requests_data = [contact_request_to_dict(cr) for cr in contact_requests]
    
    return {
        "success": True,
        "data": contact_requests_data,
        "pagination": {
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "has_next": skip + limit < total_count
        },
        "message": "Запросы обратной связи получены"
    }


@router.get("/admin/stats", response_model=dict)
def get_contact_requests_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить статистику запросов обратной связи
    """
    status_counts = crud_contact_request.count_by_status(db)
    total_count = crud_contact_request.count(db)
    recent_count = len(crud_contact_request.get_recent(db, days=7))
    
    return {
        "success": True,
        "data": {
            "total_requests": total_count,
            "recent_requests": recent_count,
            "status_distribution": status_counts
        },
        "message": "Статистика получена"
    }


@router.get("/admin/new", response_model=dict)
def get_new_contact_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить новые запросы обратной связи
    """
    contact_requests = crud_contact_request.get_new_requests(db, skip=skip, limit=limit)
    contact_requests_data = [contact_request_to_dict(cr) for cr in contact_requests]
    
    return {
        "success": True,
        "data": contact_requests_data,
        "message": "Новые запросы получены"
    }


@router.get("/admin/in-progress", response_model=dict)
def get_in_progress_contact_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить запросы в работе
    """
    contact_requests = crud_contact_request.get_in_progress_requests(db, skip=skip, limit=limit)
    contact_requests_data = [contact_request_to_dict(cr) for cr in contact_requests]
    
    return {
        "success": True,
        "data": contact_requests_data,
        "message": "Запросы в работе получены"
    }


@router.get("/admin/{request_id}", response_model=dict)
def get_contact_request_admin(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить запрос обратной связи по ID
    """
    contact_request = crud_contact_request.get(db, id=request_id)
    if not contact_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запрос не найден"
        )
    
    return {
        "success": True,
        "data": contact_request_to_dict(contact_request),
        "message": "Запрос получен"
    }


@router.put("/admin/{request_id}", response_model=dict)
def update_contact_request_admin(
    request_id: int,
    update_data: ContactRequestAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Обновить запрос обратной связи (статус и заметки администратора)
    """
    contact_request = crud_contact_request.admin_update(
        db, request_id=request_id, update_data=update_data
    )
    
    if not contact_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запрос не найден"
        )
    
    return {
        "success": True,
        "data": contact_request_to_dict(contact_request),
        "message": "Запрос обновлен"
    }


@router.put("/admin/{request_id}/status", response_model=dict)
def update_contact_request_status(
    request_id: int,
    status: ContactStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Обновить статус запроса обратной связи
    """
    contact_request = crud_contact_request.update_status(
        db, request_id=request_id, status=status
    )
    
    if not contact_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запрос не найден"
        )
    
    status_messages = {
        ContactStatus.NEW: "новый",
        ContactStatus.IN_PROGRESS: "в работе",
        ContactStatus.RESOLVED: "решен",
        ContactStatus.CLOSED: "закрыт"
    }
    
    return {
        "success": True,
        "data": contact_request_to_dict(contact_request),
        "message": f"Статус запроса изменен на '{status_messages.get(status, status.value)}'"
    }


@router.put("/admin/{request_id}/notes", response_model=dict)
def add_admin_notes(
    request_id: int,
    notes: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Добавить заметки администратора к запросу
    """
    contact_request = crud_contact_request.add_admin_notes(
        db, request_id=request_id, notes=notes
    )
    
    if not contact_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запрос не найден"
        )
    
    return {
        "success": True,
        "data": contact_request_to_dict(contact_request),
        "message": "Заметки администратора добавлены"
    }


@router.delete("/admin/{request_id}", response_model=dict)
def delete_contact_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Удалить запрос обратной связи
    """
    contact_request = crud_contact_request.get(db, id=request_id)
    if not contact_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запрос не найден"
        )
    
    crud_contact_request.remove(db, id=request_id)
    
    return {
        "success": True,
        "data": None,
        "message": "Запрос удален"
    }


@router.get("/admin/search", response_model=dict)
def search_contact_requests(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Поиск запросов обратной связи по содержимому
    """
    contact_requests = crud_contact_request.search_by_content(
        db, search_term=q, skip=skip, limit=limit
    )
    contact_requests_data = [contact_request_to_dict(cr) for cr in contact_requests]
    
    return {
        "success": True,
        "data": contact_requests_data,
        "message": f"Найдено запросов: {len(contact_requests_data)}"
    }


@router.get("/admin/by-email/{email}", response_model=dict)
def get_contact_requests_by_email(
    email: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить запросы обратной связи по email
    """
    contact_requests = crud_contact_request.get_by_email(
        db, email=email, skip=skip, limit=limit
    )
    contact_requests_data = [contact_request_to_dict(cr) for cr in contact_requests]
    
    return {
        "success": True,
        "data": contact_requests_data,
        "message": f"Запросы от {email} получены"
    }


@router.get("/admin/recent", response_model=dict)
def get_recent_contact_requests(
    days: int = Query(7, ge=1, le=365),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить недавние запросы обратной связи
    """
    contact_requests = crud_contact_request.get_recent(
        db, days=days, skip=skip, limit=limit
    )
    contact_requests_data = [contact_request_to_dict(cr) for cr in contact_requests]
    
    return {
        "success": True,
        "data": contact_requests_data,
        "message": f"Запросы за последние {days} дней получены"
    }