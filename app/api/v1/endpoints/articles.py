from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_admin_user, get_current_user_optional
from app.crud import article as crud_article
from app.models.user import User
from app.schemas.article import Article, ArticleCreate, ArticleUpdate
from app.services.cache_service import cache_service, CacheKeys

router = APIRouter()


@router.get("/", response_model=dict)
async def get_articles(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Получить список статей
    Для обычных пользователей - только опубликованные
    Для администраторов - все статьи
    """
    # Create cache key based on user role and parameters
    is_admin = current_user and current_user.role == "admin"
    cache_key_data = {
        "skip": skip,
        "limit": limit,
        "status_filter": status_filter if is_admin else None,
        "category_filter": category_filter,
        "is_admin": is_admin
    }
    import hashlib
    cache_key_str = f"{skip}:{limit}:{status_filter}:{category_filter}:{is_admin}"
    cache_key_hash = hashlib.md5(cache_key_str.encode()).hexdigest()
    cache_key = f"articles:list:{cache_key_hash}"
    
    # Try to get from cache first
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        return cached_result
    
    # Если пользователь не админ, показываем только опубликованные статьи
    if not is_admin:
        # Используем специальный метод для получения опубликованных статей
        articles = crud_article.get_published(db, skip=skip, limit=limit)
    else:
        articles = crud_article.get_multi(
            db, 
            skip=skip, 
            limit=limit, 
            status_filter=status_filter,
            category_filter=category_filter
        )
    
    # Преобразуем модели SQLAlchemy в словари для сериализации
    articles_data = []
    for article in articles:
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
        articles_data.append(article_dict)
    
    result = {
        "success": True,
        "data": articles_data,
        "message": "Статьи успешно получены"
    }
    
    # Cache the result for 10 minutes
    await cache_service.set(cache_key, result, 600)
    
    return result


@router.get("/{article_id}", response_model=dict)
async def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Получить статью по ID
    """
    # Try to get from cache first (only for published articles)
    cache_key = CacheKeys.article_detail(article_id)
    cached_article = await cache_service.get(cache_key)
    if cached_article and (not current_user or current_user.role != "admin"):
        # Increment views for cached articles
        crud_article.increment_views(db, article_id=article_id)
        return {
            "success": True,
            "data": cached_article,
            "message": "Статья успешно получена"
        }
    
    article = crud_article.get(db, id=article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Статья не найдена"
        )
    
    # Если статья не опубликована и пользователь не админ
    if not article.is_published and (not current_user or current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Статья не найдена"
        )
    
    # Увеличиваем счетчик просмотров для опубликованных статей
    if article.is_published:
        crud_article.increment_views(db, article_id=article_id)
    
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
    
    # Cache published articles for 30 minutes
    if article.is_published:
        await cache_service.set(cache_key, article_dict, 1800)
    
    return {
        "success": True,
        "data": article_dict,
        "message": "Статья успешно получена"
    }


@router.post("/", response_model=dict)
def create_article(
    article_in: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Создать новую статью (только для администраторов)
    """
    article = crud_article.create(db, obj_in=article_in)
    
    article_dict = {
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "excerpt": article.excerpt,
        "featured_image": article.featured_image,
        "category": article.category,
        "status": article.status or "draft",
        "views": article.views or 0,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
        "published_at": article.published_at,
        "is_published": article.is_published,
        "slug": article.slug,
        "tags": article.tags
    }
    
    return {
        "success": True,
        "data": article_dict,
        "message": "Статья успешно создана"
    }


@router.put("/{article_id}", response_model=dict)
def update_article(
    article_id: int,
    article_update: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Обновить статью (только для администраторов)
    """
    article = crud_article.get(db, id=article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Статья не найдена"
        )
    
    article = crud_article.update(db, db_obj=article, obj_in=article_update)
    
    article_dict = {
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "excerpt": article.excerpt,
        "featured_image": article.featured_image,
        "category": article.category,
        "status": article.status or "draft",
        "views": article.views or 0,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
        "published_at": article.published_at,
        "is_published": article.is_published,
        "slug": article.slug,
        "tags": article.tags
    }
    
    return {
        "success": True,
        "data": article_dict,
        "message": "Статья успешно обновлена"
    }


@router.delete("/{article_id}", response_model=dict)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Удалить статью (только для администраторов)
    """
    article = crud_article.get(db, id=article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Статья не найдена"
        )
    
    crud_article.remove(db, id=article_id)
    return {
        "success": True,
        "data": None,
        "message": "Статья успешно удалена"
    }