from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    role = Column(String(20), default="user")  # "user" or "admin"
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    orders = relationship("Order", back_populates="customer")