from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    def get_by_slug(self, db: Session, *, slug: str) -> Optional[Category]:
        """Get category by slug."""
        return db.query(Category).filter(Category.slug == slug).first()

    def get_by_type(self, db: Session, *, type: str, skip: int = 0, limit: int = 100) -> List[Category]:
        """Get categories by type."""
        return (
            db.query(Category)
            .filter(Category.type == type, Category.is_active == True)
            .order_by(Category.name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Category]:
        """Get active categories."""
        return (
            db.query(Category)
            .filter(Category.is_active == True)
            .order_by(Category.name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_name(self, db: Session, *, name: str, skip: int = 0, limit: int = 100) -> List[Category]:
        """Search categories by name."""
        return (
            db.query(Category)
            .filter(Category.name.contains(name), Category.is_active == True)
            .order_by(Category.name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def deactivate(self, db: Session, *, id: int) -> Optional[Category]:
        """Deactivate a category instead of deleting it."""
        category = db.query(Category).filter(Category.id == id).first()
        if category:
            category.is_active = False
            db.commit()
            db.refresh(category)
        return category

    def activate(self, db: Session, *, id: int) -> Optional[Category]:
        """Activate a category."""
        category = db.query(Category).filter(Category.id == id).first()
        if category:
            category.is_active = True
            db.commit()
            db.refresh(category)
        return category

category = CRUDCategory(Category)