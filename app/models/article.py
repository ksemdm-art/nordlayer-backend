from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Integer
from .base import BaseModel

class Article(BaseModel):
    __tablename__ = "articles"
    
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    featured_image = Column(String(255), nullable=True)
    category = Column(String(50), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    is_published = Column(Boolean, default=False)
    status = Column(String(20), default="draft")  # "draft" or "published"
    slug = Column(String(255), unique=True, index=True, nullable=False)
    tags = Column(JSON, nullable=True)  # Список тегов в формате JSON
    views = Column(Integer, default=0)  # Счетчик просмотров