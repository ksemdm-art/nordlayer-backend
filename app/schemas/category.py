from pydantic import BaseModel, field_validator
from typing import Optional
from .base import BaseSchema, TimestampedSchema

class CategoryBase(BaseSchema):
    name: str
    description: Optional[str] = None
    slug: str
    is_active: bool = True
    type: str
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed_types = ['article', 'project', 'service']
        if v not in allowed_types:
            raise ValueError(f'Type must be one of: {", ".join(allowed_types)}')
        return v

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None
    is_active: Optional[bool] = None
    type: Optional[str] = None
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v is not None:
            allowed_types = ['article', 'project', 'service']
            if v not in allowed_types:
                raise ValueError(f'Type must be one of: {", ".join(allowed_types)}')
        return v

class CategorySummary(TimestampedSchema, CategoryBase):
    pass

class Category(CategorySummary):
    pass