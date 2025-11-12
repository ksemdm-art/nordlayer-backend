from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from .base import BaseSchema, TimestampedSchema
from app.models.project import ComplexityLevel

class ProjectImageBase(BaseSchema):
    image_path: str
    alt_text: Optional[str] = None
    is_primary: bool = False

class ProjectImageCreate(ProjectImageBase):
    pass

class ProjectImage(TimestampedSchema, ProjectImageBase):
    project_id: int

class ProjectBase(BaseSchema):
    title: str
    description: Optional[str] = None
    category: str
    is_featured: bool = False
    project_metadata: Optional[Dict[str, Any]] = None
    
    # New pricing and duration fields
    estimated_price: Optional[Decimal] = None
    estimated_duration_hours: Optional[int] = None
    complexity_level: Optional[ComplexityLevel] = None
    price_range_min: Optional[Decimal] = None
    price_range_max: Optional[Decimal] = None

class ProjectCreate(ProjectBase):
    stl_file: Optional[str] = None
    images: Optional[List[str]] = []

class ProjectUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_featured: Optional[bool] = None
    stl_file: Optional[str] = None
    images: Optional[List[str]] = None
    project_metadata: Optional[Dict[str, Any]] = None
    
    # New pricing and duration fields
    estimated_price: Optional[Decimal] = None
    estimated_duration_hours: Optional[int] = None
    complexity_level: Optional[ComplexityLevel] = None
    price_range_min: Optional[Decimal] = None
    price_range_max: Optional[Decimal] = None

class ProjectSummary(TimestampedSchema, ProjectBase):
    stl_file: Optional[str] = None
    images: Optional[List[str]] = []

class Project(ProjectSummary):
    pass