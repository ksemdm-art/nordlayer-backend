from sqlalchemy import Column, String, Text, Boolean, Numeric, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel

class Service(BaseModel):
    __tablename__ = "services"
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    category = Column(String(50), nullable=True)
    features = Column(JSON, nullable=True)  # List of service features instead of price factors
    icon = Column(String(50), nullable=True, default='cube')  # Icon identifier for frontend
    
    # Relationships
    orders = relationship("Order", back_populates="service")