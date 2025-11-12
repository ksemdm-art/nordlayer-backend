from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from .base import BaseSchema, TimestampedSchema

class ContentBase(BaseSchema):
    key: str
    content_type: str = "text"
    content: Optional[str] = None
    json_content: Optional[Any] = None
    description: Optional[str] = None
    group_name: Optional[str] = None
    is_active: bool = True
    sort_order: str = "0"

class ContentCreate(ContentBase):
    pass

class ContentUpdate(BaseSchema):
    key: Optional[str] = None
    content_type: Optional[str] = None
    content: Optional[str] = None
    json_content: Optional[Any] = None
    description: Optional[str] = None
    group_name: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[str] = None

class Content(TimestampedSchema, ContentBase):
    pass

class PageBase(BaseSchema):
    slug: str
    title: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    content: Optional[Any] = None
    is_active: bool = True
    page_type: str = "custom"

class PageCreate(PageBase):
    pass

class PageUpdate(BaseSchema):
    slug: Optional[str] = None
    title: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    content: Optional[Any] = None
    is_active: Optional[bool] = None
    page_type: Optional[str] = None

class Page(TimestampedSchema, PageBase):
    pass

# Специальные схемы для группировки контента
class ContentGroup(BaseSchema):
    group_name: str
    items: List[Content]

class ContentByKey(BaseSchema):
    """Схема для получения контента по ключам"""
    contents: Dict[str, Any]