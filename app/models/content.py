from sqlalchemy import Column, String, Text, JSON, Boolean
from .base import BaseModel

class Content(BaseModel):
    __tablename__ = "content"
    
    # Уникальный ключ для идентификации контента (например: "home.hero.title")
    key = Column(String(255), unique=True, index=True, nullable=False)
    
    # Тип контента: text, html, json, image_url
    content_type = Column(String(50), default="text", nullable=False)
    
    # Основное содержимое
    content = Column(Text, nullable=True)
    
    # JSON данные для сложных структур
    json_content = Column(JSON, nullable=True)
    
    # Описание для админов
    description = Column(String(500), nullable=True)
    
    # Группировка контента (например: "home", "services", "about")
    group_name = Column(String(100), nullable=True)
    
    # Активен ли контент
    is_active = Column(Boolean, default=True)
    
    # Порядок сортировки в группе
    sort_order = Column(String(10), default="0")

class Page(BaseModel):
    __tablename__ = "pages"
    
    # Уникальный slug страницы
    slug = Column(String(255), unique=True, index=True, nullable=False)
    
    # Название страницы
    title = Column(String(255), nullable=False)
    
    # SEO заголовок
    meta_title = Column(String(255), nullable=True)
    
    # SEO описание
    meta_description = Column(Text, nullable=True)
    
    # Содержимое страницы в JSON формате
    content = Column(JSON, nullable=True)
    
    # Активна ли страница
    is_active = Column(Boolean, default=True)
    
    # Тип страницы (home, service, about, custom)
    page_type = Column(String(50), default="custom")