from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class Category(BaseModel):
    __tablename__ = "categories"
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    type = Column(String(20), nullable=False)  # 'article' or 'project' or 'service'
    
    def __repr__(self):
        return f"<Category(name='{self.name}', type='{self.type}')>"