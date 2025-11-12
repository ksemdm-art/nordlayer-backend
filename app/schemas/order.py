from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from .base import BaseSchema, TimestampedSchema, OrderStatus, OrderSource

class OrderFileBase(BaseSchema):
    original_filename: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None

class OrderFileCreate(OrderFileBase):
    file_path: str

class OrderFile(TimestampedSchema, OrderFileBase):
    file_path: str
    order_id: int

class OrderBase(BaseSchema):
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    customer_contact: Optional[str] = None  # Legacy field
    alternative_contact: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    delivery_needed: Optional[str] = None  # 'true' or 'false' as string
    delivery_details: Optional[str] = None

class OrderCreate(OrderBase):
    service_id: int
    source: OrderSource
    customer_id: Optional[int] = None

class OrderUpdate(BaseSchema):
    status: Optional[OrderStatus] = None
    total_price: Optional[Decimal] = None
    notes: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None

class OrderSummary(TimestampedSchema, OrderBase):
    status: OrderStatus
    total_price: Optional[Decimal] = None
    source: OrderSource
    service_id: int

class Order(OrderSummary):
    files: List[OrderFile] = []
    customer_id: Optional[int] = None

class OrderWithService(Order):
    service: "ServiceSummary"

class OrderWithCustomer(Order):
    customer: Optional["UserSummary"] = None