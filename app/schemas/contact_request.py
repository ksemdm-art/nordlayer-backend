from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum
from .base import BaseSchema, TimestampedSchema

class ContactStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class ContactRequestBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)

class ContactRequestCreate(ContactRequestBase):
    pass

class ContactRequestUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    subject: Optional[str] = Field(None, min_length=1, max_length=200)
    message: Optional[str] = Field(None, min_length=1)
    status: Optional[ContactStatus] = None
    admin_notes: Optional[str] = None

class ContactRequestAdminUpdate(BaseSchema):
    status: Optional[ContactStatus] = None
    admin_notes: Optional[str] = None

class ContactRequest(TimestampedSchema, ContactRequestBase):
    status: ContactStatus = ContactStatus.NEW
    admin_notes: Optional[str] = None

class ContactRequestSummary(BaseSchema):
    id: int
    name: str
    email: str
    subject: str
    status: ContactStatus
    created_at: datetime