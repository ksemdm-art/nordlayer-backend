from typing import List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate

class CRUDService(CRUDBase[Service, ServiceCreate, ServiceUpdate]):
    def get_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get active services."""
        return (
            db.query(Service)
            .filter(Service.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_category(self, db: Session, *, category: str, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get services by category."""
        return (
            db.query(Service)
            .filter(Service.category == category, Service.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_name(self, db: Session, *, name: str) -> Service:
        """Get service by exact name."""
        return db.query(Service).filter(Service.name == name).first()

    def search_by_name(self, db: Session, *, name: str, skip: int = 0, limit: int = 100) -> List[Service]:
        """Search services by name."""
        return (
            db.query(Service)
            .filter(Service.name.contains(name), Service.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def deactivate(self, db: Session, *, id: int) -> Service:
        """Deactivate a service instead of deleting it."""
        service = db.query(Service).filter(Service.id == id).first()
        if service:
            service.is_active = False
            db.commit()
            db.refresh(service)
        return service

    def activate(self, db: Session, *, id: int) -> Service:
        """Activate a service."""
        service = db.query(Service).filter(Service.id == id).first()
        if service:
            service.is_active = True
            db.commit()
            db.refresh(service)
        return service
    
    def hard_delete(self, db: Session, *, id: int) -> bool:
        """Permanently delete a service."""
        service = db.query(Service).filter(Service.id == id).first()
        if service:
            db.delete(service)
            db.commit()
            return True
        return False

service = CRUDService(Service)