from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .base import BaseSchema, TimestampedSchema

class ArticleBase(BaseSchema):
    title: str
    content: str
    excerpt: Optional[str] = None
    category: str
    is_published: bool = False
    status: str = "draft"
    slug: str
    tags: Optional[List[str]] = None

class ArticleCreate(ArticleBase):
    featured_image: Optional[str] = None
    published_at: Optional[datetime] = None

class ArticleUpdate(BaseSchema):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    category: Optional[str] = None
    is_published: Optional[bool] = None
    status: Optional[str] = None
    slug: Optional[str] = None
    published_at: Optional[datetime] = None
    tags: Optional[List[str]] = None

class ArticleSummary(TimestampedSchema, ArticleBase):
    featured_image: Optional[str] = None
    published_at: Optional[datetime] = None
    views: int = 0

class Article(ArticleSummary):
    pass