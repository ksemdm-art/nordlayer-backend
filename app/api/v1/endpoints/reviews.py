from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import json

from app.core.deps import get_db, get_current_admin_user
from app.crud import review as crud_review
from app.models.user import User
from app.schemas.review import (
    Review, ReviewCreate, ReviewUpdate, ReviewModerationUpdate, 
    ReviewSummary, ReviewImageBase
)
from app.services.s3_manager import s3_manager

router = APIRouter()


def review_to_dict(review) -> dict:
    """Convert Review model to dictionary for API response"""
    return {
        "id": review.id,
        "customer_name": review.customer_name,
        "customer_email": review.customer_email,
        "rating": review.rating,
        "title": review.title,
        "content": review.content,
        "images": review.images or [],
        "is_approved": review.is_approved,
        "is_featured": review.is_featured,
        "created_at": review.created_at,
        "updated_at": review.updated_at
    }


@router.get("/", response_model=dict)
def get_reviews(
    skip: int = 0,
    limit: int = 100,
    approved_only: bool = True,
    featured_only: bool = False,
    rating: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Получить список отзывов (публичный endpoint)
    По умолчанию возвращает только одобренные отзывы
    """
    if rating and (rating < 1 or rating > 5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Рейтинг должен быть от 1 до 5"
        )
    
    if rating:
        reviews = crud_review.get_by_rating(
            db, rating=rating, skip=skip, limit=limit
        )
    elif featured_only:
        reviews = crud_review.get_featured(db, skip=skip, limit=limit)
    else:
        reviews = crud_review.get_multi(
            db, skip=skip, limit=limit, 
            approved_only=approved_only, featured_only=featured_only
        )
    
    reviews_data = [review_to_dict(review) for review in reviews]
    
    return {
        "success": True,
        "data": reviews_data,
        "message": "Отзывы успешно получены"
    }


@router.get("/stats", response_model=dict)
def get_review_stats(db: Session = Depends(get_db)):
    """
    Получить статистику отзывов (публичный endpoint)
    """
    average_rating = crud_review.get_average_rating(db)
    rating_distribution = crud_review.get_rating_distribution(db)
    total_reviews = crud_review.count(db, approved_only=True)
    
    return {
        "success": True,
        "data": {
            "average_rating": round(average_rating, 1),
            "rating_distribution": rating_distribution,
            "total_reviews": total_reviews
        },
        "message": "Статистика отзывов получена"
    }


@router.get("/featured", response_model=dict)
def get_featured_reviews(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Получить рекомендуемые отзывы (публичный endpoint)
    """
    reviews = crud_review.get_featured(db, skip=skip, limit=limit)
    reviews_data = [review_to_dict(review) for review in reviews]
    
    return {
        "success": True,
        "data": reviews_data,
        "message": "Рекомендуемые отзывы получены"
    }


@router.get("/{review_id}", response_model=dict)
def get_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить отзыв по ID (публичный endpoint для одобренных отзывов)
    """
    review = crud_review.get(db, id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отзыв не найден"
        )
    
    # Для публичного доступа показываем только одобренные отзывы
    if not review.is_approved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отзыв не найден"
        )
    
    return {
        "success": True,
        "data": review_to_dict(review),
        "message": "Отзыв получен"
    }


@router.post("/", response_model=dict)
async def create_review(
    customer_name: str = Form(...),
    customer_email: str = Form(...),
    rating: int = Form(..., ge=1, le=5),
    content: str = Form(...),
    title: Optional[str] = Form(None),
    images: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db)
):
    """
    Создать новый отзыв (публичный endpoint)
    Поддерживает загрузку изображений
    """
    
    # Загружаем изображения в S3 если они есть
    uploaded_images = []
    if images and s3_manager:
        for i, image in enumerate(images):
            if image.filename:  # Проверяем что файл не пустой
                try:
                    # Загружаем изображение в S3
                    image_url = await s3_manager.upload_file(
                        image, 
                        f"uploads/reviews/{customer_email}",
                        validate=True
                    )
                    uploaded_images.append({
                        "url": image_url,
                        "caption": f"Изображение {i + 1}"
                    })
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ошибка загрузки изображения: {str(e)}"
                    )
    
    # Создаем отзыв
    review_data = ReviewCreate(
        customer_name=customer_name,
        customer_email=customer_email,
        rating=rating,
        title=title,
        content=content,
        images=[ReviewImageBase(**img) for img in uploaded_images] if uploaded_images else None
    )
    
    try:
        review = crud_review.create(db, obj_in=review_data)
        return {
            "success": True,
            "data": review_to_dict(review),
            "message": "Отзыв создан и отправлен на модерацию"
        }
    except Exception as e:
        # Если создание отзыва не удалось, удаляем загруженные изображения
        if uploaded_images and s3_manager:
            for img in uploaded_images:
                s3_manager.delete_file(img["url"])
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка создания отзыва: {str(e)}"
        )


# Административные endpoints

@router.get("/admin/all", response_model=dict)
def get_all_reviews_admin(
    skip: int = 0,
    limit: int = 100,
    approved_only: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить все отзывы для администратора
    """
    if approved_only is None:
        reviews = crud_review.get_multi(db, skip=skip, limit=limit)
    else:
        reviews = crud_review.get_multi(
            db, skip=skip, limit=limit, approved_only=approved_only
        )
    
    reviews_data = [review_to_dict(review) for review in reviews]
    
    return {
        "success": True,
        "data": reviews_data,
        "message": "Отзывы получены"
    }


@router.get("/admin/pending", response_model=dict)
def get_pending_reviews(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить отзывы, ожидающие модерации
    """
    reviews = crud_review.get_pending_moderation(db, skip=skip, limit=limit)
    reviews_data = [review_to_dict(review) for review in reviews]
    
    return {
        "success": True,
        "data": reviews_data,
        "message": "Отзывы на модерации получены"
    }


@router.get("/admin/{review_id}", response_model=dict)
def get_review_admin(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить отзыв по ID для администратора (включая неодобренные)
    """
    review = crud_review.get(db, id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отзыв не найден"
        )
    
    return {
        "success": True,
        "data": review_to_dict(review),
        "message": "Отзыв получен"
    }


@router.put("/admin/{review_id}/moderate", response_model=dict)
def moderate_review(
    review_id: int,
    moderation_data: ReviewModerationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Модерировать отзыв (одобрить/отклонить, сделать рекомендуемым)
    """
    review = crud_review.moderate_review(
        db, review_id=review_id, moderation_data=moderation_data
    )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отзыв не найден"
        )
    
    return {
        "success": True,
        "data": review_to_dict(review),
        "message": "Статус отзыва обновлен"
    }


@router.put("/admin/{review_id}/approve", response_model=dict)
def approve_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Одобрить отзыв
    """
    review = crud_review.approve_review(db, review_id=review_id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отзыв не найден"
        )
    
    return {
        "success": True,
        "data": review_to_dict(review),
        "message": "Отзыв одобрен"
    }


@router.put("/admin/{review_id}/reject", response_model=dict)
def reject_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Отклонить отзыв
    """
    review = crud_review.reject_review(db, review_id=review_id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отзыв не найден"
        )
    
    return {
        "success": True,
        "data": review_to_dict(review),
        "message": "Отзыв отклонен"
    }


@router.put("/admin/{review_id}/feature", response_model=dict)
def set_review_featured(
    review_id: int,
    featured: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Сделать отзыв рекомендуемым или убрать из рекомендуемых
    """
    review = crud_review.set_featured(db, review_id=review_id, featured=featured)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отзыв не найден или не одобрен"
        )
    
    action = "добавлен в рекомендуемые" if featured else "убран из рекомендуемых"
    return {
        "success": True,
        "data": review_to_dict(review),
        "message": f"Отзыв {action}"
    }


@router.put("/admin/{review_id}", response_model=dict)
def update_review_admin(
    review_id: int,
    review_update: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Обновить отзыв (только для администраторов)
    """
    review = crud_review.get(db, id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отзыв не найден"
        )
    
    review = crud_review.update(db, db_obj=review, obj_in=review_update)
    
    return {
        "success": True,
        "data": review_to_dict(review),
        "message": "Отзыв обновлен"
    }


@router.delete("/admin/{review_id}", response_model=dict)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Удалить отзыв (только для администраторов)
    """
    review = crud_review.get(db, id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отзыв не найден"
        )
    
    # Удаляем изображения из S3 если они есть
    if review.images and s3_manager:
        for image in review.images:
            if isinstance(image, dict) and 'url' in image:
                s3_manager.delete_file(image['url'])
    
    crud_review.remove(db, id=review_id)
    
    return {
        "success": True,
        "data": None,
        "message": "Отзыв удален"
    }


@router.get("/admin/search", response_model=dict)
def search_reviews(
    q: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Поиск отзывов по содержимому или заголовку
    """
    reviews = crud_review.search_by_content(
        db, search_term=q, skip=skip, limit=limit
    )
    reviews_data = [review_to_dict(review) for review in reviews]
    
    return {
        "success": True,
        "data": reviews_data,
        "message": f"Найдено отзывов: {len(reviews_data)}"
    }