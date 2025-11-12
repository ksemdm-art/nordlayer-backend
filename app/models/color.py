from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, JSON, Float
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from .base import BaseModel


class ColorType(str, PyEnum):
    SOLID = "solid"
    GRADIENT = "gradient"
    METALLIC = "metallic"


class Color(BaseModel):
    __tablename__ = "colors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    type = Column(Enum(ColorType), default=ColorType.SOLID, nullable=False)
    
    # For solid colors
    hex_code = Column(String(7), nullable=True)  # #FFFFFF format
    
    # For gradients
    gradient_colors = Column(JSON, nullable=True)  # [{"color": "#FF0000", "position": 0}, ...]
    gradient_direction = Column(String(20), nullable=True)  # linear, radial
    
    # For metallics
    metallic_base = Column(String(7), nullable=True)
    metallic_intensity = Column(Float, nullable=True)  # 0.0 - 1.0
    
    # Common properties
    is_active = Column(Boolean, default=True, nullable=False)
    is_new = Column(Boolean, default=False, nullable=False)  # Новинка
    sort_order = Column(Integer, default=0, nullable=False)
    price_modifier = Column(Float, default=1.0, nullable=False)  # Price multiplier
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())