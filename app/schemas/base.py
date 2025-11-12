from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class OrderStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OrderSource(str, Enum):
    WEB = "web"
    TELEGRAM = "telegram"

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class TimestampedSchema(BaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    pagination: Optional[Dict[str, Any]] = None