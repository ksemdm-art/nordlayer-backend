import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_admin_user
from app.crud import order as crud_order
from app.models.user import User
from app.schemas.order import Order, OrderCreate, OrderUpdate
from app.services.notification import notification_service
from app.core.performance import (
    performance_tracker, 
    cache_manager, 
    DatabaseOptimizer, 
    ResponseOptimizer
)

router = APIRouter()
logger = logging.getLogger(__name__)


def order_to_dict(order) -> dict:
    """Convert Order model to dictionary for API response"""
    specs = order.specifications or {}
    
    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "customer_email": getattr(order, 'customer_email', None) or order.customer_contact,  # Fallback for legacy data
        "customer_phone": getattr(order, 'customer_phone', None) or specs.get("customer_phone"),
        "customer_contact": order.customer_contact,  # Legacy field
        "alternative_contact": getattr(order, 'alternative_contact', None),
        "service_id": order.service_id,
        "service_name": specs.get("service_type"),
        "status": order.status,
        "total_price": order.total_price,
        "source": order.source,
        "notes": order.notes,
        "specifications": order.specifications,
        "delivery_needed": getattr(order, 'delivery_needed', None),
        "delivery_details": getattr(order, 'delivery_details', None),
        
        # Извлекаем данные из specifications для удобства
        "color": specs.get("color"),
        "color_name": specs.get("colorName"),
        "multi_color": specs.get("isMultiColor", False),
        "multi_colors": specs.get("multiColors", []),
        "quantity": specs.get("quantity", 1),
        "infill": specs.get("infill"),
        "material": specs.get("material"),
        "quality": specs.get("quality"),
        "urgency": specs.get("urgency"),
        
        # Файлы и галерея
        "files_info": specs.get("files_info", []),
        "selected_gallery_items": specs.get("selected_gallery_items", []),
        
        # Доставка и оплата (legacy fields from specifications)
        "delivery_method": specs.get("deliveryMethod"),
        "payment_method": specs.get("paymentMethod"),
        "delivery_address": specs.get("deliveryAddress"),
        "delivery_city": specs.get("deliveryCity"),
        "delivery_postal_code": specs.get("deliveryPostalCode"),
        
        "created_at": order.created_at,
        "updated_at": order.updated_at
    }


@router.get("/", response_model=dict)
def get_orders(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить список всех заказов (только для администраторов)
    """
    orders = crud_order.get_multi(
        db, skip=skip, limit=limit, status_filter=status_filter
    )
    
    # Преобразуем модели SQLAlchemy в словари для сериализации
    orders_data = [order_to_dict(order) for order in orders]
    
    return {
        "success": True,
        "data": orders_data,
        "message": "Заказы успешно получены"
    }


@router.get("/{order_id}", response_model=dict)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить заказ по ID (только для администраторов)
    """
    order = crud_order.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    return {
        "success": True,
        "data": order_to_dict(order),
        "message": "Заказ успешно получен"
    }


@router.post("/", response_model=dict)
async def create_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Создать новый заказ (публичный endpoint)
    """
    try:
        print(f"Received order data: {order_data}")
        print(f"Order data dict: {order_data.model_dump()}")
        
        # Создаем заказ
        order = crud_order.create(db, obj_in=order_data)
        order_dict = order_to_dict(order)
        
        # Send notifications in background
        background_tasks.add_task(notification_service.notify_new_order, order_dict)
        
        return {
            "success": True,
            "data": order_dict,
            "message": "Заказ успешно создан"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка создания заказа: {str(e)}"
        )


@router.put("/{order_id}", response_model=dict)
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Обновить заказ (только для администраторов)
    """
    order = crud_order.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Store old status for comparison
    old_status = order.status
    
    # Update order
    order = crud_order.update(db, db_obj=order, obj_in=order_update)
    order_dict = order_to_dict(order)
    
    # Check if status changed and send notification
    new_status = order.status
    if old_status != new_status:
        logger.info(f"Order {order_id} status changed from {old_status} to {new_status}")
        # Send status change notifications in background
        background_tasks.add_task(notification_service.notify_status_change, order_dict)
    
    return {
        "success": True,
        "data": order_dict,
        "message": "Заказ успешно обновлен"
    }


@router.get("/search", response_model=dict)
def search_orders_by_email(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Поиск заказов по email клиента (публичный endpoint для отслеживания)
    """
    if not email or "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректный email адрес"
        )
    
    orders = crud_order.get_by_email(db, email=email)
    
    # Преобразуем модели SQLAlchemy в словари для сериализации
    orders_data = [order_to_dict(order) for order in orders]
    
    return {
        "success": True,
        "data": orders_data,
        "message": f"Найдено заказов: {len(orders_data)}"
    }


@router.post("/webhook/status-change", response_model=dict)
def webhook_status_change(
    order_id: int,
    new_status: str,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Webhook для уведомления о изменении статуса заказа
    Используется для отправки уведомлений в Telegram бот
    """
    order = crud_order.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Log the webhook call
    logger.info(f"Status change webhook called for order {order_id}: {new_status}")
    
    # In a real implementation, this would trigger a notification to the telegram bot
    # For now, we'll just return success
    return {
        "success": True,
        "message": f"Webhook processed for order {order_id}",
        "data": {
            "order_id": order_id,
            "new_status": new_status,
            "user_id": user_id
        }
    }


@router.delete("/{order_id}", response_model=dict)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Удалить заказ (только для администраторов)
    """
    order = crud_order.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    crud_order.remove(db, id=order_id)
    return {
        "success": True,
        "data": None,
        "message": "Заказ успешно удален"
    }