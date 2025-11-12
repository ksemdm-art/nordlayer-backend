from sqlalchemy import Column, String, Text, Boolean, JSON, Integer, ForeignKey, Numeric, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class ComplexityLevel(str, enum.Enum):
    SIMPLE = "simple"      # 1-3 часа
    MEDIUM = "medium"      # 4-8 часов  
    COMPLEX = "complex"    # 9+ часов

class Project(BaseModel):
    __tablename__ = "projects"
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    stl_file = Column(String(255), nullable=True)
    is_featured = Column(Boolean, default=False)
    images = Column(JSON, nullable=True, default=list)  # Simple array of image URLs
    project_metadata = Column(JSON, nullable=True)  # For additional project data
    
    # New pricing and duration fields
    estimated_price = Column(Numeric(10, 2), nullable=True)
    estimated_duration_hours = Column(Integer, nullable=True)
    complexity_level = Column(Enum(ComplexityLevel), nullable=True)
    
    # Price range fields for grouping by complexity
    price_range_min = Column(Numeric(10, 2), nullable=True)
    price_range_max = Column(Numeric(10, 2), nullable=True)

class ProjectImage(BaseModel):
    __tablename__ = "project_images"
    
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    image_path = Column(String(255), nullable=False)
    alt_text = Column(String(200), nullable=True)
    is_primary = Column(Boolean, default=False)