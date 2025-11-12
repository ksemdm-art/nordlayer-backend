from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from datetime import datetime, timedelta
from app.crud.base import CRUDBase
from app.models.contact_request import ContactRequest, ContactStatus
from app.schemas.contact_request import ContactRequestCreate, ContactRequestUpdate, ContactRequestAdminUpdate

class CRUDContactRequest(CRUDBase[ContactRequest, ContactRequestCreate, ContactRequestUpdate]):
    
    def get_by_status(self, db: Session, *, status: ContactStatus, skip: int = 0, limit: int = 100) -> List[ContactRequest]:
        """Get contact requests by status."""
        return (
            db.query(ContactRequest)
            .filter(ContactRequest.status == status)
            .order_by(desc(ContactRequest.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_email(self, db: Session, *, email: str, skip: int = 0, limit: int = 100) -> List[ContactRequest]:
        """Get contact requests by email."""
        return (
            db.query(ContactRequest)
            .filter(ContactRequest.email == email)
            .order_by(desc(ContactRequest.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_date_range(
        self, 
        db: Session, 
        *, 
        start_date: datetime, 
        end_date: datetime, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ContactRequest]:
        """Get contact requests within a date range."""
        return (
            db.query(ContactRequest)
            .filter(and_(
                ContactRequest.created_at >= start_date,
                ContactRequest.created_at <= end_date
            ))
            .order_by(desc(ContactRequest.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_recent(self, db: Session, *, days: int = 7, skip: int = 0, limit: int = 100) -> List[ContactRequest]:
        """Get recent contact requests from the last N days."""
        start_date = datetime.utcnow() - timedelta(days=days)
        return (
            db.query(ContactRequest)
            .filter(ContactRequest.created_at >= start_date)
            .order_by(desc(ContactRequest.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_new_requests(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ContactRequest]:
        """Get new contact requests."""
        return self.get_by_status(db, status=ContactStatus.NEW, skip=skip, limit=limit)
    
    def get_in_progress_requests(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ContactRequest]:
        """Get in-progress contact requests."""
        return self.get_by_status(db, status=ContactStatus.IN_PROGRESS, skip=skip, limit=limit)
    
    def get_resolved_requests(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ContactRequest]:
        """Get resolved contact requests."""
        return self.get_by_status(db, status=ContactStatus.RESOLVED, skip=skip, limit=limit)
    
    def get_closed_requests(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ContactRequest]:
        """Get closed contact requests."""
        return self.get_by_status(db, status=ContactStatus.CLOSED, skip=skip, limit=limit)
    
    def update_status(self, db: Session, *, request_id: int, status: ContactStatus) -> Optional[ContactRequest]:
        """Update the status of a contact request."""
        contact_request = db.query(ContactRequest).filter(ContactRequest.id == request_id).first()
        if contact_request:
            contact_request.status = status
            db.commit()
            db.refresh(contact_request)
        return contact_request
    
    def add_admin_notes(self, db: Session, *, request_id: int, notes: str) -> Optional[ContactRequest]:
        """Add admin notes to a contact request."""
        contact_request = db.query(ContactRequest).filter(ContactRequest.id == request_id).first()
        if contact_request:
            contact_request.admin_notes = notes
            db.commit()
            db.refresh(contact_request)
        return contact_request
    
    def admin_update(self, db: Session, *, request_id: int, update_data: ContactRequestAdminUpdate) -> Optional[ContactRequest]:
        """Update contact request with admin data."""
        contact_request = db.query(ContactRequest).filter(ContactRequest.id == request_id).first()
        if contact_request:
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(contact_request, field, value)
            db.commit()
            db.refresh(contact_request)
        return contact_request
    
    def search_by_content(self, db: Session, *, search_term: str, skip: int = 0, limit: int = 100) -> List[ContactRequest]:
        """Search contact requests by name, subject, or message content."""
        return (
            db.query(ContactRequest)
            .filter(
                (ContactRequest.name.contains(search_term)) |
                (ContactRequest.subject.contains(search_term)) |
                (ContactRequest.message.contains(search_term))
            )
            .order_by(desc(ContactRequest.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_multi_filtered(
        self,
        db: Session,
        *,
        status: Optional[ContactStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search_term: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[ContactRequest]:
        """Get contact requests with multiple filters."""
        query = db.query(ContactRequest)
        
        # Apply filters
        if status:
            query = query.filter(ContactRequest.status == status)
        
        if start_date:
            query = query.filter(ContactRequest.created_at >= start_date)
        
        if end_date:
            query = query.filter(ContactRequest.created_at <= end_date)
        
        if search_term:
            query = query.filter(
                (ContactRequest.name.contains(search_term)) |
                (ContactRequest.subject.contains(search_term)) |
                (ContactRequest.message.contains(search_term))
            )
        
        # Apply ordering
        order_column = getattr(ContactRequest, order_by, ContactRequest.created_at)
        if order_desc:
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        return query.offset(skip).limit(limit).all()
    
    def count_by_status(self, db: Session) -> dict:
        """Get count of contact requests by status."""
        from sqlalchemy import func
        results = (
            db.query(ContactRequest.status, func.count(ContactRequest.id))
            .group_by(ContactRequest.status)
            .all()
        )
        return {status.value: count for status, count in results}
    
    def count_filtered(
        self,
        db: Session,
        *,
        status: Optional[ContactStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search_term: Optional[str] = None
    ) -> int:
        """Count contact requests with filters."""
        query = db.query(ContactRequest)
        
        if status:
            query = query.filter(ContactRequest.status == status)
        
        if start_date:
            query = query.filter(ContactRequest.created_at >= start_date)
        
        if end_date:
            query = query.filter(ContactRequest.created_at <= end_date)
        
        if search_term:
            query = query.filter(
                (ContactRequest.name.contains(search_term)) |
                (ContactRequest.subject.contains(search_term)) |
                (ContactRequest.message.contains(search_term))
            )
        
        return query.count()

contact_request = CRUDContactRequest(ContactRequest)