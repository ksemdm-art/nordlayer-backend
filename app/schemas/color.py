from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ColorType(str, Enum):
    SOLID = "solid"
    GRADIENT = "gradient"
    METALLIC = "metallic"


class GradientStop(BaseModel):
    color: str = Field(..., pattern=r'^#[0-9A-Fa-f]{6}$')
    position: float = Field(..., ge=0, le=100)


class ColorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: ColorType = ColorType.SOLID
    is_active: bool = True
    is_new: bool = False
    sort_order: int = 0
    price_modifier: float = Field(1.0, gt=0)
    
    # For solid colors
    hex_code: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    
    # For gradients
    gradient_colors: Optional[List[GradientStop]] = None
    gradient_direction: Optional[str] = Field(None, pattern=r'^(linear|radial)$')
    
    # For metallics
    metallic_base: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    metallic_intensity: Optional[float] = Field(None, ge=0, le=1)

    @validator('hex_code')
    def validate_hex_code_for_solid(cls, v, values):
        if values.get('type') == ColorType.SOLID and not v:
            raise ValueError('Solid colors must have a hex_code')
        return v

    @validator('gradient_colors')
    def validate_gradient_colors(cls, v, values):
        if values.get('type') == ColorType.GRADIENT:
            if not v or len(v) < 2:
                raise ValueError('Gradient colors must have at least 2 color stops')
        return v

    @validator('gradient_direction')
    def validate_gradient_direction(cls, v, values):
        if values.get('type') == ColorType.GRADIENT and not v:
            return 'linear'  # Default value
        return v

    @validator('metallic_base')
    def validate_metallic_base(cls, v, values):
        if values.get('type') == ColorType.METALLIC and not v:
            raise ValueError('Metallic colors must have a metallic_base')
        return v

    @validator('metallic_intensity')
    def validate_metallic_intensity(cls, v, values):
        if values.get('type') == ColorType.METALLIC and v is None:
            return 0.5  # Default value
        return v


class ColorCreate(ColorBase):
    pass


class ColorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[ColorType] = None
    is_active: Optional[bool] = None
    is_new: Optional[bool] = None
    sort_order: Optional[int] = None
    price_modifier: Optional[float] = Field(None, gt=0)
    
    # For solid colors
    hex_code: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    
    # For gradients
    gradient_colors: Optional[List[GradientStop]] = None
    gradient_direction: Optional[str] = Field(None, pattern=r'^(linear|radial)$')
    
    # For metallics
    metallic_base: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    metallic_intensity: Optional[float] = Field(None, ge=0, le=1)


class ColorInDB(ColorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Color(ColorInDB):
    pass


# Response schemas for different color types
class SolidColorResponse(BaseModel):
    id: int
    name: str
    type: ColorType
    hex_code: str
    is_active: bool
    is_new: bool
    sort_order: int
    price_modifier: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GradientColorResponse(BaseModel):
    id: int
    name: str
    type: ColorType
    gradient_colors: List[GradientStop]
    gradient_direction: str
    is_active: bool
    is_new: bool
    sort_order: int
    price_modifier: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MetallicColorResponse(BaseModel):
    id: int
    name: str
    type: ColorType
    metallic_base: str
    metallic_intensity: float
    is_active: bool
    is_new: bool
    sort_order: int
    price_modifier: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True