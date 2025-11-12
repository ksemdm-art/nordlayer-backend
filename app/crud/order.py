from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.order import Order, OrderFile
from app.schemas.order import OrderCreate, OrderUpdate, OrderFileCreate
from app.schemas.base import OrderStatus, OrderSource

class CRUDOrder(CRUDBase[Order, OrderCreate, OrderUpdate]):
    def create(self, db: Session, *, obj_in: OrderCreate) -> Order:
        """Create order with automatic customer_contact fallback."""
        obj_in_data = obj_in.model_dump()
        
        # If customer_contact is not provided, use customer_email as fallback
        if not obj_in_data.get('customer_contact') and obj_in_data.get('customer_email'):
            obj_in_data['customer_contact'] = obj_in_data['customer_email']
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    def get_by_customer(self, db: Session, *, customer_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get orders by customer ID."""
        return (
            db.query(Order)
            .filter(Order.customer_id == customer_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(self, db: Session, *, status: OrderStatus, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get orders by status."""
        return (
            db.query(Order)
            .filter(Order.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_source(self, db: Session, *, source: OrderSource, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get orders by source (WEB or TELEGRAM)."""
        return (
            db.query(Order)
            .filter(Order.source == source)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_service(self, db: Session, *, service_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get orders by service ID."""
        return (
            db.query(Order)
            .filter(Order.service_id == service_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_status(self, db: Session, *, order_id: int, status: OrderStatus) -> Optional[Order]:
        """Update order status."""
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = status
            db.commit()
            db.refresh(order)
        return order

    def search_by_customer_name(self, db: Session, *, name: str, skip: int = 0, limit: int = 100) -> List[Order]:
        """Search orders by customer name."""
        return (
            db.query(Order)
            .filter(Order.customer_name.contains(name))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_email(self, db: Session, *, email: str) -> List[Order]:
        """Get orders by customer email."""
        return (
            db.query(Order)
            .filter(Order.customer_email == email)
            .order_by(Order.created_at.desc())
            .all()
        )

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        status_filter: Optional[str] = None
    ):
        """Get multiple orders with optional filtering."""
        query = db.query(self.model)
        
        if status_filter:
            query = query.filter(self.model.status == status_filter)
        
        return query.order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()

class CRUDOrderFile(CRUDBase[OrderFile, OrderFileCreate, OrderFileCreate]):
    def get_by_order(self, db: Session, *, order_id: int) -> List[OrderFile]:
        """Get all files for an order."""
        return db.query(OrderFile).filter(OrderFile.order_id == order_id).all()

    def get_by_file_type(self, db: Session, *, file_type: str, skip: int = 0, limit: int = 100) -> List[OrderFile]:
        """Get files by type."""
        return (
            db.query(OrderFile)
            .filter(OrderFile.file_type == file_type)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def delete_by_order(self, db: Session, *, order_id: int) -> int:
        """Delete all files for an order."""
        count = db.query(OrderFile).filter(OrderFile.order_id == order_id).count()
        db.query(OrderFile).filter(OrderFile.order_id == order_id).delete()
        db.commit()
        return count

order = CRUDOrder(Order)
order_file = CRUDOrderFile(OrderFile)