from sqlalchemy import Column, String, Text, Integer, Boolean, JSON
from .base import BaseModel

class Review(BaseModel):
    __tablename__ = "reviews"
    
    # Убираем связь с заказами - отзывы теперь независимы
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(200), nullable=False)
    
    rating = Column(Integer, nullable=False)  # 1-5
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    
    # Изображения результата
    images = Column(JSON, nullable=True)  # [{"url": "s3://...", "caption": "..."}]
    
    is_approved = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)