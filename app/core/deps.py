"""
Dependency injection for FastAPI
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.auth import verify_token
from app.core.exceptions import AuthenticationError
from app.crud.user import user as user_crud
from app.models.user import User

security = HTTPBearer(auto_error=False)


def get_db() -> Generator:
    """Database session dependency"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token (optional)"""
    if not credentials:
        return None
    
    payload = verify_token(credentials.credentials)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = user_crud.get(db, id=int(user_id))
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token (required)"""
    if not credentials:
        raise AuthenticationError("Authentication credentials required")
    
    payload = verify_token(credentials.credentials)
    if not payload:
        raise AuthenticationError("Invalid authentication token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid authentication token")
    
    user = user_crud.get(db, id=int(user_id))
    if not user:
        raise AuthenticationError("User not found")
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current admin user (required admin role)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user