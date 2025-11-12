from typing import Any, Dict, Optional, Union
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.auth import get_password_hash, verify_password

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create user with hashed password."""
        hashed_password = get_password_hash(obj_in.password)
        
        # Set role based on is_admin flag or explicit role
        role = getattr(obj_in, 'role', 'user')
        if getattr(obj_in, 'is_admin', False):
            role = 'admin'
        
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=hashed_password,
            full_name=obj_in.full_name,
            is_active=obj_in.is_active,
            is_admin=getattr(obj_in, 'is_admin', False),
            role=role,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """Update user, handling password hashing if needed."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
            
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active

    def is_admin(self, user: User) -> bool:
        """Check if user is admin."""
        return user.is_admin

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        role_filter: Optional[str] = None,
        status_filter: Optional[str] = None
    ):
        """Get multiple users with optional filtering."""
        query = db.query(self.model)
        
        if role_filter:
            query = query.filter(self.model.role == role_filter)
        
        if status_filter:
            if status_filter == "active":
                query = query.filter(self.model.is_active == True)
            elif status_filter == "inactive":
                query = query.filter(self.model.is_active == False)
        
        return query.order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()

    def create_admin(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create admin user."""
        hashed_password = get_password_hash(obj_in.password)
        
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=hashed_password,
            full_name=obj_in.full_name,
            is_active=True,
            is_admin=True,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

user = CRUDUser(User)