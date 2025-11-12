from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from .base import BaseSchema, TimestampedSchema

class ReviewImageBase(BaseModel):
    url: str
    caption: Optional[str] = None

class ReviewBase(BaseSchema):
    customer_name: str
    customer_email: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    title: Optional[str] = None
    content: str
    images: Optional[List[ReviewImageBase]] = None

class ReviewCreate(ReviewBase):
    pass  # Убираем order_id

class ReviewUpdate(BaseSchema):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = None
    content: Optional[str] = None
    images: Optional[List[ReviewImageBase]] = None
    is_approved: Optional[bool] = None
    is_featured: Optional[bool] = None

class ReviewModerationUpdate(BaseSchema):
    is_approved: Optional[bool] = None
    is_featured: Optional[bool] = None

class Review(TimestampedSchema, ReviewBase):
    is_approved: bool = False
    is_featured: bool = False

class ReviewSummary(BaseSchema):
    id: int
    customer_name: str
    rating: int
    title: Optional[str] = None
    content: str
    images: Optional[List[ReviewImageBase]] = None
    is_featured: bool = False
    created_at: datetime