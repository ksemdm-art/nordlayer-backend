from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_admin_user, get_current_user_optional
from app.crud import content as crud_content
from app.models.user import User
from app.schemas.content import Content, ContentCreate, ContentUpdate, Page, PageCreate, PageUpdate, ContentByKey

router = APIRouter()

# Публичные endpoints для получения контента
@router.get("/content/by-keys", response_model=dict)
def get_content_by_keys(
    keys: str,  # Comma-separated list of keys
    db: Session = Depends(get_db)
):
    """
    Получить контент по списку ключей (публичный endpoint)
    """
    key_list = [key.strip() for key in keys.split(",") if key.strip()]
    content_dict = crud_content.content.get_content_dict(db, keys=key_list)
    
    return {
        "success": True,
        "data": content_dict,
        "message": "Контент успешно получен"
    }

@router.get("/content/by-group/{group_name}", response_model=dict)
def get_content_by_group(
    group_name: str,
    db: Session = Depends(get_db)
):
    """
    Получить весь контент группы (публичный endpoint)
    """
    content_dict = crud_content.content.get_content_dict(db, group_name=group_name)
    
    return {
        "success": True,
        "data": content_dict,
        "message": f"Контент группы {group_name} успешно получен"
    }

@router.get("/pages/{slug}", response_model=dict)
def get_page_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Получить страницу по slug (публичный endpoint)
    """
    page = crud_content.page.get_by_slug(db, slug=slug)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Страница не найдена"
        )
    
    page_dict = {
        "id": page.id,
        "slug": page.slug,
        "title": page.title,
        "meta_title": page.meta_title,
        "meta_description": page.meta_description,
        "content": page.content,
        "page_type": page.page_type,
        "created_at": page.created_at,
        "updated_at": page.updated_at
    }
    
    return {
        "success": True,
        "data": page_dict,
        "message": "Страница успешно получена"
    }

# Админские endpoints для управления контентом
@router.get("/admin/content", response_model=dict)
def get_all_content(
    skip: int = 0,
    limit: int = 100,
    group_filter: Optional[str] = None,
    content_type_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить весь контент для админ-панели
    """
    contents = crud_content.content.get_multi(
        db, 
        skip=skip, 
        limit=limit, 
        group_filter=group_filter,
        content_type_filter=content_type_filter
    )
    
    # Преобразуем в словари для сериализации
    contents_data = []
    for content in contents:
        content_dict = {
            "id": content.id,
            "key": content.key,
            "content_type": content.content_type,
            "content": content.content,
            "json_content": content.json_content,
            "description": content.description,
            "group_name": content.group_name,
            "is_active": content.is_active,
            "sort_order": content.sort_order,
            "created_at": content.created_at,
            "updated_at": content.updated_at
        }
        contents_data.append(content_dict)
    
    return {
        "success": True,
        "data": contents_data,
        "message": "Контент успешно получен"
    }

@router.get("/admin/content/groups", response_model=dict)
def get_content_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить список всех групп контента
    """
    groups = crud_content.content.get_all_groups(db)
    
    return {
        "success": True,
        "data": groups,
        "message": "Группы контента успешно получены"
    }

@router.post("/admin/content", response_model=dict)
def create_content(
    content_in: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Создать новый контент
    """
    # Проверяем, не существует ли уже контент с таким ключом
    existing = crud_content.content.get_by_key(db, key=content_in.key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Контент с таким ключом уже существует"
        )
    
    content = crud_content.content.create(db, obj_in=content_in)
    
    content_dict = {
        "id": content.id,
        "key": content.key,
        "content_type": content.content_type,
        "content": content.content,
        "json_content": content.json_content,
        "description": content.description,
        "group_name": content.group_name,
        "is_active": content.is_active,
        "sort_order": content.sort_order,
        "created_at": content.created_at,
        "updated_at": content.updated_at
    }
    
    return {
        "success": True,
        "data": content_dict,
        "message": "Контент успешно создан"
    }

@router.put("/admin/content/{content_id}", response_model=dict)
def update_content(
    content_id: int,
    content_update: ContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Обновить контент
    """
    content = crud_content.content.get(db, id=content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Контент не найден"
        )
    
    content = crud_content.content.update(db, db_obj=content, obj_in=content_update)
    
    content_dict = {
        "id": content.id,
        "key": content.key,
        "content_type": content.content_type,
        "content": content.content,
        "json_content": content.json_content,
        "description": content.description,
        "group_name": content.group_name,
        "is_active": content.is_active,
        "sort_order": content.sort_order,
        "created_at": content.created_at,
        "updated_at": content.updated_at
    }
    
    return {
        "success": True,
        "data": content_dict,
        "message": "Контент успешно обновлен"
    }

@router.delete("/admin/content/{content_id}", response_model=dict)
def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Удалить контент
    """
    content = crud_content.content.get(db, id=content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Контент не найден"
        )
    
    crud_content.content.remove(db, id=content_id)
    
    return {
        "success": True,
        "data": None,
        "message": "Контент успешно удален"
    }

# Endpoints для управления страницами
@router.get("/admin/pages", response_model=dict)
def get_all_pages(
    skip: int = 0,
    limit: int = 100,
    page_type_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить все страницы для админ-панели
    """
    pages = crud_content.page.get_multi(
        db, 
        skip=skip, 
        limit=limit, 
        page_type_filter=page_type_filter
    )
    
    # Преобразуем в словари для сериализации
    pages_data = []
    for page in pages:
        page_dict = {
            "id": page.id,
            "slug": page.slug,
            "title": page.title,
            "meta_title": page.meta_title,
            "meta_description": page.meta_description,
            "content": page.content,
            "is_active": page.is_active,
            "page_type": page.page_type,
            "created_at": page.created_at,
            "updated_at": page.updated_at
        }
        pages_data.append(page_dict)
    
    return {
        "success": True,
        "data": pages_data,
        "message": "Страницы успешно получены"
    }

@router.post("/admin/pages", response_model=dict)
def create_page(
    page_in: PageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Создать новую страницу
    """
    # Проверяем, не существует ли уже страница с таким slug
    existing = crud_content.page.get_by_slug(db, slug=page_in.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Страница с таким slug уже существует"
        )
    
    page = crud_content.page.create(db, obj_in=page_in)
    
    page_dict = {
        "id": page.id,
        "slug": page.slug,
        "title": page.title,
        "meta_title": page.meta_title,
        "meta_description": page.meta_description,
        "content": page.content,
        "is_active": page.is_active,
        "page_type": page.page_type,
        "created_at": page.created_at,
        "updated_at": page.updated_at
    }
    
    return {
        "success": True,
        "data": page_dict,
        "message": "Страница успешно создана"
    }

@router.put("/admin/pages/{page_id}", response_model=dict)
def update_page(
    page_id: int,
    page_update: PageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Обновить страницу
    """
    page = crud_content.page.get(db, id=page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Страница не найдена"
        )
    
    page = crud_content.page.update(db, db_obj=page, obj_in=page_update)
    
    page_dict = {
        "id": page.id,
        "slug": page.slug,
        "title": page.title,
        "meta_title": page.meta_title,
        "meta_description": page.meta_description,
        "content": page.content,
        "is_active": page.is_active,
        "page_type": page.page_type,
        "created_at": page.created_at,
        "updated_at": page.updated_at
    }
    
    return {
        "success": True,
        "data": page_dict,
        "message": "Страница успешно обновлена"
    }

@router.delete("/admin/pages/{page_id}", response_model=dict)
def delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Удалить страницу
    """
    page = crud_content.page.get(db, id=page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Страница не найдена"
        )
    
    crud_content.page.remove(db, id=page_id)
    
    return {
        "success": True,
        "data": None,
        "message": "Страница успешно удалена"
    }