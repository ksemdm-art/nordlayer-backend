from pydantic import BaseModel
from decimal import Decimal
from typing import Dict, Any, Optional, List
from .base import BaseSchema, TimestampedSchema

class ServiceBase(BaseSchema):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    category: Optional[str] = None
    features: Optional[List[str]] = None
    icon: Optional[str] = 'cube'

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None
    features: Optional[List[str]] = None
    icon: Optional[str] = None

class ServiceSummary(TimestampedSchema, ServiceBase):
    pass

class Service(ServiceSummary):
    pass