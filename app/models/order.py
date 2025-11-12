from sqlalchemy import Column, String, Text, Numeric, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Order(BaseModel):
    __tablename__ = "orders"
    
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(200), nullable=False)
    customer_phone = Column(String(50), nullable=True)  # Made optional
    customer_contact = Column(String(200), nullable=True)  # Legacy field, now optional
    alternative_contact = Column(String(200), nullable=True)  # New field for alternative contact
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Optional for anonymous orders
    specifications = Column(JSON, nullable=True)
    status = Column(String(20), default="new")
    total_price = Column(Numeric(10, 2), nullable=True)
    source = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    delivery_needed = Column(String(10), nullable=True)  # 'true' or 'false' as string
    delivery_details = Column(Text, nullable=True)  # Delivery address and details
    
    # Relationships
    service = relationship("Service", back_populates="orders")
    customer = relationship("User", back_populates="orders")
    files = relationship("OrderFile", back_populates="order", cascade="all, delete-orphan")

class OrderFile(BaseModel):
    __tablename__ = "order_files"
    
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    file_path = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(50), nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="files")