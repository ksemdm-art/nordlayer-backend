from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_admin_user
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate

router = APIRouter()


@router.get("/", response_model=dict)
def get_users(
    skip: int = 0,
    limit: int = 100,
    role_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить список всех пользователей (только для администраторов)
    """
    users = crud_user.get_multi(
        db, 
        skip=skip, 
        limit=limit, 
        role_filter=role_filter,
        status_filter=status_filter
    )
    
    # Преобразуем модели SQLAlchemy в словари для сериализации
    users_data = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "role": user.role or ("admin" if user.is_admin else "user"),
            "last_login": user.last_login,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        users_data.append(user_dict)
    
    return {
        "success": True,
        "data": users_data,
        "message": "Пользователи успешно получены"
    }


@router.get("/{user_id}", response_model=dict)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить пользователя по ID (только для администраторов)
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "role": user.role or ("admin" if user.is_admin else "user"),
        "last_login": user.last_login,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    
    return {
        "success": True,
        "data": user_dict,
        "message": "Пользователь успешно получен"
    }


@router.post("/", response_model=dict)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Создать нового пользователя (только для администраторов)
    """
    # Проверяем, не существует ли уже пользователь с таким email
    existing_user = crud_user.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    user = crud_user.create(db, obj_in=user_in)
    
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "role": user.role or ("admin" if user.is_admin else "user"),
        "last_login": user.last_login,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    
    return {
        "success": True,
        "data": user_dict,
        "message": "Пользователь успешно создан"
    }


@router.put("/{user_id}", response_model=dict)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Обновить пользователя (только для администраторов)
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Проверяем, что админ не деактивирует сам себя
    if user_id == current_user.id and hasattr(user_update, 'is_active') and not user_update.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя деактивировать собственную учетную запись"
        )
    
    user = crud_user.update(db, db_obj=user, obj_in=user_update)
    
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "role": user.role or ("admin" if user.is_admin else "user"),
        "last_login": user.last_login,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    
    return {
        "success": True,
        "data": user_dict,
        "message": "Пользователь успешно обновлен"
    }


@router.delete("/{user_id}", response_model=dict)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Удалить пользователя (только для администраторов)
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить собственную учетную запись"
        )
    
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    crud_user.remove(db, id=user_id)
    return {
        "success": True,
        "data": None,
        "message": "Пользователь успешно удален"
    }