from sqlalchemy import Column, String, Text, Enum as SQLEnum
from enum import Enum
from .base import BaseModel

class ContactStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class ContactRequest(BaseModel):
    __tablename__ = "contact_requests"
    
    name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    status = Column(SQLEnum(ContactStatus), default=ContactStatus.NEW)
    admin_notes = Column(Text, nullable=True)