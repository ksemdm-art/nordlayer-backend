from sqlalchemy import Column, String, Text, Boolean, JSON
from .base import BaseModel

class SiteSetting(BaseModel):
    __tablename__ = "site_settings"
    
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default="text")  # text, json, boolean, number
    description = Column(Text, nullable=True)
    category = Column(String(50), default="general")  # general, homepage, services, contact, etc.
    is_public = Column(Boolean, default=True)  # Can be accessed by frontend

class PageContent(BaseModel):
    __tablename__ = "page_contents"
    
    page_key = Column(String(100), nullable=False, index=True)  # homepage, services, about, etc.
    section_key = Column(String(100), nullable=False)  # hero, features, pricing, etc.
    content_type = Column(String(20), default="text")  # text, html, json
    content = Column(Text, nullable=True)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    order_index = Column(String(10), default="0")
    is_active = Column(Boolean, default=True)
    
    # Unique constraint on page_key + section_key
    __table_args__ = (
        {'sqlite_autoincrement': True}
    )