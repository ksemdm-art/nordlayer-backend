from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, get_current_admin_user
from app.core.auth import create_access_token, verify_password
from app.core.config import settings
from app.crud.user import user as user_crud
from app.schemas.auth import LoginRequest, LoginResponse, ChangePasswordRequest
from app.schemas.user import User, UserCreate, UserUpdate
from app.models.user import User as UserModel

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Admin login endpoint."""
    user = user_crud.authenticate(
        db, email=login_data.email, password=login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires,
        is_admin=user.is_admin
    )
    
    return LoginResponse(
        access_token=access_token,
        user=User.model_validate(user)
    )

@router.post("/login/token", response_model=LoginResponse)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible token login endpoint."""
    user = user_crud.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires,
        is_admin=user.is_admin
    )
    
    return LoginResponse(
        access_token=access_token,
        user=User.model_validate(user)
    )

@router.get("/me", response_model=User)
def read_current_user(
    current_user: UserModel = Depends(get_current_user)
):
    """Get current user info."""
    return User.model_validate(current_user)

@router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user password."""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    user_crud.update(
        db,
        db_obj=current_user,
        obj_in={"password": password_data.new_password}
    )
    
    return {"message": "Password updated successfully"}

# Admin-only endpoints for user management
@router.get("/users", response_model=List[User])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    users = user_crud.get_multi(db, skip=skip, limit=limit)
    return [User.model_validate(user) for user in users]

@router.post("/users", response_model=User)
def create_user(
    user_in: UserCreate,
    current_admin: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create new user (admin only)."""
    # Check if user already exists
    existing_user = user_crud.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    existing_username = user_crud.get_by_username(db, username=user_in.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists"
        )
    
    user = user_crud.create(db, obj_in=user_in)
    return User.model_validate(user)

@router.get("/users/{user_id}", response_model=User)
def get_user(
    user_id: int,
    current_admin: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only)."""
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return User.model_validate(user)

@router.put("/users/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_admin: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user (admin only)."""
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check for email conflicts
    if user_in.email and user_in.email != user.email:
        existing_user = user_crud.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
    
    # Check for username conflicts
    if user_in.username and user_in.username != user.username:
        existing_username = user_crud.get_by_username(db, username=user_in.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username already exists"
            )
    
    user = user_crud.update(db, db_obj=user, obj_in=user_in)
    return User.model_validate(user)

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_admin: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)."""
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deleting themselves
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user_crud.remove(db, id=user_id)
    return {"message": "User deleted successfully"}